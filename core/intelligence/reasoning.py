"""
Reasoning Engine
================
The brain of DataNarrative.
Orchestrates: Query Analysis → Retrieval → Insight Detection → Narrative

This is the main intelligence orchestrator.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from .analyzer import QueryAnalyzer, QueryAnalysis, QueryIntent
from .detector import InsightDetector, DetectedInsight, InsightType
from .narrator import NarrativeGenerator, Narrative

logger = logging.getLogger(__name__)


@dataclass
class ReasoningResult:
    """Complete result of the reasoning process"""
    # Input
    query: str
    query_analysis: QueryAnalysis
    
    # Retrieved context
    context_found: bool
    context_summary: str
    sources_used: List[str]
    
    # Insights
    insights: List[DetectedInsight]
    primary_insight: Optional[DetectedInsight]
    
    # Output decision
    output_mode: str              # "story" or "data"
    recommended_template: str
    
    # Narrative (if story mode)
    narrative: Optional[Narrative] = None
    
    # For rendering
    render_data: Dict = field(default_factory=dict)
    
    # Confidence
    overall_confidence: float = 0.0
    reasoning_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "intent": self.query_analysis.intent.value,
            "domain": self.query_analysis.domain_hint,
            "context_found": self.context_found,
            "context_summary": self.context_summary,
            "sources": self.sources_used,
            "insights_count": len(self.insights),
            "primary_insight": self.primary_insight.to_dict() if self.primary_insight else None,
            "output_mode": self.output_mode,
            "template": self.recommended_template,
            "narrative": self.narrative.to_dict() if self.narrative else None,
            "confidence": self.overall_confidence,
            "notes": self.reasoning_notes
        }


class ReasoningEngine:
    """
    Main intelligence engine that coordinates all reasoning.
    
    Flow:
    1. Analyze query to understand intent
    2. Retrieve relevant data from knowledge base
    3. Detect insights from the data
    4. Decide output mode (story vs data)
    5. Generate narrative if story mode
    6. Prepare render specifications
    
    Usage:
        engine = ReasoningEngine(knowledge_store)
        result = await engine.reason("How has literacy changed in Telangana?")
    """
    
    def __init__(
        self,
        knowledge_store=None,
        use_ai_narrator: bool = False,
        api_key: Optional[str] = None
    ):
        """
        Initialize the reasoning engine.
        
        Args:
            knowledge_store: KnowledgeStore instance for retrieval
            use_ai_narrator: Whether to use Claude for narrative generation
            api_key: Anthropic API key (if using AI)
        """
        self.knowledge_store = knowledge_store
        self.analyzer = QueryAnalyzer()
        self.detector = InsightDetector()
        self.narrator = NarrativeGenerator(use_ai=use_ai_narrator, api_key=api_key)
    
    async def reason(
        self,
        query: str,
        force_mode: Optional[str] = None,
        domain_override: Optional[str] = None
    ) -> ReasoningResult:
        """
        Main reasoning method.
        
        Args:
            query: Natural language query
            force_mode: Force "story" or "data" mode
            domain_override: Override detected domain
            
        Returns:
            Complete ReasoningResult
        """
        reasoning_notes = []
        
        # Step 1: Analyze query
        logger.info(f"Step 1: Analyzing query: '{query}'")
        analysis = self.analyzer.analyze(query)
        
        reasoning_notes.append(f"Intent detected: {analysis.intent.value}")
        reasoning_notes.append(f"Domain hint: {analysis.domain_hint}")
        reasoning_notes.append(f"Requires historical: {analysis.requires_historical}")
        
        # Step 2: Retrieve context
        logger.info("Step 2: Retrieving context")
        context_data, sources = await self._retrieve_context(analysis, domain_override)
        
        context_found = len(context_data) > 0
        context_summary = f"Found {len(context_data)} relevant data points from {len(sources)} sources"
        reasoning_notes.append(context_summary)
        
        # Step 3: Detect insights
        logger.info("Step 3: Detecting insights")
        insights = self._detect_insights(context_data, analysis)
        
        reasoning_notes.append(f"Detected {len(insights)} insights")
        
        # Step 4: Select primary insight
        primary_insight = self._select_primary_insight(insights, analysis)
        
        if primary_insight:
            reasoning_notes.append(f"Primary insight: {primary_insight.insight_type.value}")
        
        # Step 5: Decide output mode
        output_mode = self._decide_output_mode(analysis, insights, force_mode)
        reasoning_notes.append(f"Output mode: {output_mode}")
        
        # Step 6: Select template
        template = self._select_template(primary_insight, analysis, output_mode)
        reasoning_notes.append(f"Template: {template}")
        
        # Step 7: Generate narrative if story mode
        narrative = None
        if output_mode == "story" and primary_insight:
            logger.info("Step 7: Generating narrative")
            domain = domain_override or analysis.domain_hint or "general"
            source = sources[0] if sources else "Data Analysis"
            narrative = self.narrator.generate(primary_insight, domain, source)
        
        # Step 8: Prepare render data
        render_data = self._prepare_render_data(
            analysis, insights, primary_insight, narrative, template
        )
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(context_found, insights, primary_insight)
        
        return ReasoningResult(
            query=query,
            query_analysis=analysis,
            context_found=context_found,
            context_summary=context_summary,
            sources_used=sources,
            insights=insights,
            primary_insight=primary_insight,
            output_mode=output_mode,
            recommended_template=template,
            narrative=narrative,
            render_data=render_data,
            overall_confidence=confidence,
            reasoning_notes=reasoning_notes
        )
    
    async def _retrieve_context(
        self,
        analysis: QueryAnalysis,
        domain_override: Optional[str]
    ) -> tuple[List[Dict], List[str]]:
        """Retrieve relevant data from knowledge store"""
        
        if not self.knowledge_store:
            logger.warning("No knowledge store configured")
            return [], []
        
        try:
            # Import here to avoid circular dependency
            from ..knowledge import Retriever
            
            retriever = Retriever(store=self.knowledge_store)
            
            domain = domain_override or analysis.domain_hint
            
            context = await retriever.retrieve(
                query=analysis.normalized_query,
                domain_hint=domain,
                require_historical=analysis.requires_historical
            )
            
            # Extract data from results
            data = []
            sources = set()
            
            for result in context.results:
                # Try to extract structured data from content
                if hasattr(result, 'metadata') and result.metadata:
                    sources.add(result.metadata.get('source_name', 'Unknown'))
                else:
                    sources.add(result.source if hasattr(result, 'source') else 'Unknown')
                
                # Add content as data point
                data.append({
                    "content": result.content,
                    "relevance": result.relevance,
                    "domain": result.domain if hasattr(result, 'domain') else None,
                    "has_historical": result.has_historical_depth if hasattr(result, 'has_historical_depth') else False
                })
            
            return data, list(sources)
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return [], []
    
    def _detect_insights(
        self,
        context_data: List[Dict],
        analysis: QueryAnalysis
    ) -> List[DetectedInsight]:
        """Detect insights from retrieved data"""
        
        insights = []
        
        # For now, create basic insights from context
        # In production, this would parse the actual data
        
        for item in context_data:
            if item.get("has_historical"):
                # Placeholder insight for historical data
                insight = DetectedInsight(
                    insight_type=InsightType.GROWTH if "growth" in analysis.normalized_query else InsightType.STABILITY,
                    summary=f"Data analysis based on query: {analysis.original_query[:50]}",
                    metric_name=analysis.topics[0] if analysis.topics else "metric",
                    current_value=0,
                    confidence=item.get("relevance", 0.5)
                )
                insights.append(insight)
                break  # One insight per context for now
        
        return insights
    
    def _select_primary_insight(
        self,
        insights: List[DetectedInsight],
        analysis: QueryAnalysis
    ) -> Optional[DetectedInsight]:
        """Select the most relevant insight"""
        
        if not insights:
            return None
        
        # Sort by confidence and relevance to query intent
        def score_insight(insight: DetectedInsight) -> float:
            score = insight.confidence
            
            # Boost if matches query intent
            intent_match = {
                QueryIntent.TREND: [InsightType.GROWTH, InsightType.DECLINE],
                QueryIntent.COMPARISON: [InsightType.COMPARISON, InsightType.RANKING],
                QueryIntent.RANKING: [InsightType.RANKING],
                QueryIntent.CURRENT_STATE: [InsightType.STABILITY],
            }
            
            if analysis.intent in intent_match:
                if insight.insight_type in intent_match[analysis.intent]:
                    score += 0.2
            
            return score
        
        sorted_insights = sorted(insights, key=score_insight, reverse=True)
        return sorted_insights[0]
    
    def _decide_output_mode(
        self,
        analysis: QueryAnalysis,
        insights: List[DetectedInsight],
        force_mode: Optional[str]
    ) -> str:
        """Decide between story and data mode"""
        
        if force_mode:
            return force_mode
        
        # Story mode conditions:
        # 1. User asked for trends/changes (implies historical)
        # 2. We have historical data
        # 3. Strong growth/decline insight detected
        
        has_historical_insight = any(
            i.insight_type in [InsightType.GROWTH, InsightType.DECLINE]
            and i.time_range is not None
            for i in insights
        )
        
        trend_intent = analysis.intent == QueryIntent.TREND
        
        if analysis.requires_historical and (has_historical_insight or trend_intent):
            return "story"
        
        return "data"
    
    def _select_template(
        self,
        primary_insight: Optional[DetectedInsight],
        analysis: QueryAnalysis,
        output_mode: str
    ) -> str:
        """Select the best template"""
        
        if output_mode == "story":
            return "story_five_frame"
        
        if primary_insight:
            return primary_insight.recommended_template
        
        # Default based on intent
        intent_templates = {
            QueryIntent.TREND: "trend_line",
            QueryIntent.COMPARISON: "versus",
            QueryIntent.RANKING: "ranking_bar",
            QueryIntent.CURRENT_STATE: "hero_stat",
            QueryIntent.BREAKDOWN: "pie_breakdown",
        }
        
        return intent_templates.get(analysis.intent, "hero_stat")
    
    def _prepare_render_data(
        self,
        analysis: QueryAnalysis,
        insights: List[DetectedInsight],
        primary_insight: Optional[DetectedInsight],
        narrative: Optional[Narrative],
        template: str
    ) -> Dict:
        """Prepare data for rendering"""
        
        render_data = {
            "template": template,
            "domain": analysis.domain_hint or "general",
            "title": "",
            "subtitle": "",
            "metrics": [],
            "chart_data": [],
            "insights": [],
        }
        
        if narrative:
            render_data["title"] = narrative.title
            render_data["subtitle"] = narrative.subtitle
            render_data["narrative_frames"] = narrative.to_dict()["frames"]
        elif primary_insight:
            render_data["title"] = primary_insight.summary
            render_data["metrics"] = [{
                "value": primary_insight.current_value,
                "label": primary_insight.metric_name,
                "change": primary_insight.change_percentage
            }]
        
        for insight in insights:
            render_data["insights"].append({
                "type": insight.insight_type.value,
                "summary": insight.summary,
                "confidence": insight.confidence
            })
        
        return render_data
    
    def _calculate_confidence(
        self,
        context_found: bool,
        insights: List[DetectedInsight],
        primary_insight: Optional[DetectedInsight]
    ) -> float:
        """Calculate overall confidence score"""
        
        score = 0.0
        
        if context_found:
            score += 0.3
        
        if insights:
            avg_insight_confidence = sum(i.confidence for i in insights) / len(insights)
            score += avg_insight_confidence * 0.4
        
        if primary_insight:
            score += primary_insight.confidence * 0.3
        
        return min(score, 1.0)


async def reason_query(
    query: str,
    knowledge_store=None,
    force_mode: Optional[str] = None
) -> ReasoningResult:
    """Quick reasoning function"""
    engine = ReasoningEngine(knowledge_store=knowledge_store)
    return await engine.reason(query, force_mode=force_mode)
