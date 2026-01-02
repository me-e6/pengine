"""
Insight Generator
=================
Uses Claude to analyze retrieved data and generate insights.
Answers the 4 universal questions:
1. What is the data really saying?
2. What changed meaningfully?
3. Why does it matter to humans?
4. How should this be shown visually?
"""

import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ..models import (
    Insight, InsightType, Sentiment, TemplateType, 
    Domain, OutputMode
)
from ..knowledge.retriever import RetrievalContext, RetrievalResult
from .analyzer import QueryAnalysis

logger = logging.getLogger(__name__)

# Optional anthropic import
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


@dataclass
class InsightGenerationResult:
    """Result of insight generation"""
    success: bool
    insight: Optional[Insight]
    raw_analysis: Dict[str, Any]
    output_mode: OutputMode
    can_tell_story: bool
    error: Optional[str] = None


class InsightGenerator:
    """
    Generates insights from retrieved data using Claude.
    
    The insight generator:
    1. Takes retrieved context + query analysis
    2. Asks Claude to analyze the data
    3. Extracts structured insights
    4. Recommends visualization approach
    """
    
    ANALYSIS_PROMPT = '''You are an expert data analyst and storyteller. Analyze the following data and answer these questions.

USER QUERY: {query}

QUERY INTENT: {intent}
DOMAIN: {domain}

RETRIEVED DATA:
{context_data}

---

Analyze this data and respond with a JSON object containing:

{{
    "summary": "2-3 sentence summary of the key finding",
    
    "insight_type": "growth|decline|comparison|ranking|distribution|correlation|anomaly|threshold",
    
    "change_description": "What specific change occurred? Be precise with numbers.",
    
    "magnitude": "small|moderate|significant|dramatic",
    
    "direction": "up|down|stable|mixed",
    
    "velocity": "How fast is the change? e.g., '6% per year' or 'gradual' or 'rapid'",
    
    "human_impact": "Why does this matter to ordinary people? One clear sentence.",
    
    "key_metrics": [
        {{"label": "metric name", "value": "number or text", "context": "what this means"}}
    ],
    
    "evidence": [
        "Specific data point 1 with numbers",
        "Specific data point 2 with numbers"
    ],
    
    "sentiment": "positive|negative|neutral|warning",
    
    "recommended_template": "hero_stat|before_after|ranking_bar|trend_line|pie_breakdown|versus|story_five_frame",
    
    "story_potential": {{
        "can_tell_story": true/false,
        "reason": "why or why not",
        "narrative_hook": "compelling opening line for the story"
    }},
    
    "confidence": 0.0-1.0,
    
    "uncertainty_flags": ["any caveats or data quality issues"]
}}

IMPORTANT:
- Be specific with numbers, don't generalize
- If data is insufficient, say so in uncertainty_flags
- Match recommended_template to the insight_type
- story_potential.can_tell_story should be true ONLY if there's clear temporal change

Return ONLY valid JSON, no other text.'''

    NARRATIVE_PROMPT = '''You are a data storyteller. Create a 5-frame narrative from this insight.

INSIGHT: {insight_summary}
KEY FINDING: {change_description}
HUMAN IMPACT: {human_impact}

DATA CONTEXT:
{context_data}

---

Create a 5-frame story structure. Each frame should be impactful and data-driven.

Respond with JSON:
{{
    "title": "Compelling story title",
    
    "frames": [
        {{
            "frame": "context",
            "headline": "Setting the scene (max 8 words)",
            "body_text": "2-3 sentences establishing the baseline/situation",
            "key_metric": {{"label": "metric", "value": "number", "unit": "if any"}},
            "visual_suggestion": "What to show visually"
        }},
        {{
            "frame": "change", 
            "headline": "The shift/change (max 8 words)",
            "body_text": "2-3 sentences about what changed",
            "key_metric": {{"label": "metric", "value": "number", "unit": "if any"}},
            "visual_suggestion": "What to show visually"
        }},
        {{
            "frame": "evidence",
            "headline": "Proof point (max 8 words)",
            "body_text": "2-3 sentences with supporting data",
            "key_metric": {{"label": "metric", "value": "number", "unit": "if any"}},
            "visual_suggestion": "What to show visually"
        }},
        {{
            "frame": "consequence",
            "headline": "What this means (max 8 words)",
            "body_text": "2-3 sentences about implications",
            "key_metric": {{"label": "metric", "value": "number", "unit": "if any"}},
            "visual_suggestion": "What to show visually"
        }},
        {{
            "frame": "implication",
            "headline": "Looking ahead (max 8 words)",
            "body_text": "2-3 sentences about future outlook",
            "key_metric": {{"label": "metric", "value": "number", "unit": "if any"}},
            "visual_suggestion": "What to show visually"
        }}
    ]
}}

Make each frame punchy and memorable. Use specific numbers.
Return ONLY valid JSON.'''

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key"""
        self.client = None
        self.api_key = api_key
        self._init_client()
    
    def _init_client(self):
        """Initialize Anthropic client"""
        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic not installed - using mock insights")
            return
        
        try:
            if self.api_key:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            else:
                self.client = anthropic.Anthropic()
        except Exception as e:
            logger.warning(f"Could not initialize Claude: {e}")
    
    async def generate(
        self,
        query_analysis: QueryAnalysis,
        retrieval_context: RetrievalContext
    ) -> InsightGenerationResult:
        """
        Generate insights from query and retrieved data.
        
        Args:
            query_analysis: Analyzed user query
            retrieval_context: Retrieved relevant data
            
        Returns:
            InsightGenerationResult with structured insight
        """
        logger.info(f"Generating insights for: {query_analysis.original_query}")
        
        # Check if we have enough context
        if not retrieval_context.sufficient_context:
            logger.warning("Insufficient context for insight generation")
            return InsightGenerationResult(
                success=False,
                insight=None,
                raw_analysis={},
                output_mode=OutputMode.DATA,
                can_tell_story=False,
                error="Insufficient data to generate insights"
            )
        
        # Prepare context data for Claude
        context_data = self._prepare_context(retrieval_context)
        
        # Generate analysis
        if self.client:
            raw_analysis = await self._ai_analyze(query_analysis, context_data)
        else:
            raw_analysis = self._mock_analyze(query_analysis, retrieval_context)
        
        if not raw_analysis:
            return InsightGenerationResult(
                success=False,
                insight=None,
                raw_analysis={},
                output_mode=OutputMode.DATA,
                can_tell_story=False,
                error="Analysis generation failed"
            )
        
        # Convert to Insight object
        insight = self._to_insight(raw_analysis, query_analysis)
        
        # Determine output mode
        can_story = raw_analysis.get('story_potential', {}).get('can_tell_story', False)
        output_mode = OutputMode.STORY if can_story and retrieval_context.has_historical_data else OutputMode.DATA
        
        return InsightGenerationResult(
            success=True,
            insight=insight,
            raw_analysis=raw_analysis,
            output_mode=output_mode,
            can_tell_story=can_story
        )
    
    async def generate_narrative(
        self,
        insight: Insight,
        retrieval_context: RetrievalContext
    ) -> Optional[Dict]:
        """
        Generate a 5-frame narrative for Story Mode.
        
        Args:
            insight: Generated insight
            retrieval_context: Original context
            
        Returns:
            Narrative structure or None
        """
        if not self.client:
            return self._mock_narrative(insight)
        
        context_data = self._prepare_context(retrieval_context)
        
        prompt = self.NARRATIVE_PROMPT.format(
            insight_summary=insight.summary,
            change_description=insight.change_description or "Data analysis",
            human_impact=insight.human_impact or "Impacts daily life",
            context_data=context_data[:3000]
        )
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            return self._parse_json_response(response_text)
            
        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            return None
    
    def _prepare_context(self, retrieval_context: RetrievalContext) -> str:
        """Prepare retrieval context for prompt"""
        lines = []
        
        for i, result in enumerate(retrieval_context.results[:5], 1):
            lines.append(f"[Source {i}: {result.source}]")
            lines.append(f"Domain: {result.domain}")
            if result.year:
                lines.append(f"Year: {result.year}")
            if result.region:
                lines.append(f"Region: {result.region}")
            lines.append(f"Content: {result.content[:500]}")
            lines.append("")
        
        if retrieval_context.time_range:
            lines.append(f"Time Range: {retrieval_context.time_range[0]} to {retrieval_context.time_range[1]}")
        
        return "\n".join(lines)
    
    async def _ai_analyze(
        self,
        query_analysis: QueryAnalysis,
        context_data: str
    ) -> Optional[Dict]:
        """Use Claude to analyze data"""
        
        prompt = self.ANALYSIS_PROMPT.format(
            query=query_analysis.original_query,
            intent=query_analysis.primary_intent.value,
            domain=query_analysis.domain_hint or "general",
            context_data=context_data[:4000]
        )
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            return self._parse_json_response(response_text)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None
    
    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from Claude response"""
        try:
            # Clean up response
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None
    
    def _mock_analyze(
        self,
        query_analysis: QueryAnalysis,
        context: RetrievalContext
    ) -> Dict:
        """Generate mock analysis when Claude is unavailable"""
        
        # Extract some real data from context
        sample_content = context.results[0].content if context.results else "No data"
        domain = context.domains_found[0] if context.domains_found else "general"
        
        return {
            "summary": f"Analysis of {domain} data based on available sources.",
            "insight_type": query_analysis.suggested_insight_type.value,
            "change_description": "Data shows patterns that require further analysis.",
            "magnitude": "moderate",
            "direction": "mixed",
            "velocity": "gradual",
            "human_impact": f"This {domain} data affects daily life in the region.",
            "key_metrics": [
                {"label": "Data Points", "value": str(len(context.results)), "context": "sources analyzed"}
            ],
            "evidence": [sample_content[:100]],
            "sentiment": "neutral",
            "recommended_template": "hero_stat",
            "story_potential": {
                "can_tell_story": context.has_historical_data,
                "reason": "Historical data available" if context.has_historical_data else "No time series",
                "narrative_hook": f"Understanding {domain} in the region"
            },
            "confidence": 0.5,
            "uncertainty_flags": ["Mock analysis - install anthropic for real insights"]
        }
    
    def _mock_narrative(self, insight: Insight) -> Dict:
        """Generate mock narrative"""
        return {
            "title": f"The Story of {insight.summary[:30]}...",
            "frames": [
                {
                    "frame": "context",
                    "headline": "Where We Started",
                    "body_text": "Setting the baseline for understanding.",
                    "key_metric": {"label": "Baseline", "value": "—", "unit": ""},
                    "visual_suggestion": "Starting point visualization"
                },
                {
                    "frame": "change",
                    "headline": "What Changed",
                    "body_text": insight.change_description or "Significant changes occurred.",
                    "key_metric": {"label": "Change", "value": "—", "unit": ""},
                    "visual_suggestion": "Before/after comparison"
                },
                {
                    "frame": "evidence",
                    "headline": "The Proof",
                    "body_text": "Data supports this finding.",
                    "key_metric": {"label": "Evidence", "value": "—", "unit": ""},
                    "visual_suggestion": "Supporting data chart"
                },
                {
                    "frame": "consequence",
                    "headline": "Why It Matters",
                    "body_text": insight.human_impact or "This affects daily life.",
                    "key_metric": {"label": "Impact", "value": "—", "unit": ""},
                    "visual_suggestion": "Impact visualization"
                },
                {
                    "frame": "implication",
                    "headline": "Looking Forward",
                    "body_text": "Future implications to consider.",
                    "key_metric": {"label": "Outlook", "value": "—", "unit": ""},
                    "visual_suggestion": "Future projection"
                }
            ]
        }
    
    def _to_insight(self, raw: Dict, query: QueryAnalysis) -> Insight:
        """Convert raw analysis to Insight object"""
        
        # Parse insight type
        try:
            insight_type = InsightType(raw.get('insight_type', 'comparison'))
        except ValueError:
            insight_type = InsightType.COMPARISON
        
        # Parse sentiment
        try:
            sentiment = Sentiment(raw.get('sentiment', 'neutral'))
        except ValueError:
            sentiment = Sentiment.NEUTRAL
        
        # Parse template
        try:
            template = TemplateType(raw.get('recommended_template', 'hero_stat'))
        except ValueError:
            template = TemplateType.HERO_STAT
        
        return Insight(
            summary=raw.get('summary', 'No summary available'),
            insight_type=insight_type,
            change_description=raw.get('change_description'),
            magnitude=raw.get('magnitude'),
            direction=raw.get('direction'),
            velocity=raw.get('velocity'),
            human_impact=raw.get('human_impact'),
            recommended_template=template,
            sentiment=sentiment,
            evidence_chunks=[],  # Would link to actual chunks
            confidence=raw.get('confidence', 0.5),
            uncertainty_flags=raw.get('uncertainty_flags', [])
        )


# === Convenience function ===
async def generate_insight(
    query_analysis: QueryAnalysis,
    retrieval_context: RetrievalContext,
    api_key: Optional[str] = None
) -> InsightGenerationResult:
    """Quick insight generation"""
    generator = InsightGenerator(api_key=api_key)
    return await generator.generate(query_analysis, retrieval_context)
