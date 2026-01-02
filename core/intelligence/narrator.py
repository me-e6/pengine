"""
Narrative Generator
===================
Generates 5-frame story narratives from insights.
Creates compelling data stories that answer:
- Context: What's the background?
- Change: What happened?
- Evidence: What proves it?
- Consequence: What does it mean?
- Implication: What's next?
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from .detector import DetectedInsight, InsightType, Sentiment

logger = logging.getLogger(__name__)


@dataclass
class StoryFrame:
    """A single frame in the 5-frame narrative"""
    frame_type: str              # context, change, evidence, consequence, implication
    headline: str                # Bold headline
    body_text: str               # Supporting text
    key_metric: Optional[str]    # Featured number/stat
    key_metric_label: str        # Label for the metric
    visual_hint: str             # What visual to show
    emphasis: str                # What to emphasize visually


@dataclass
class Narrative:
    """Complete 5-frame story"""
    title: str
    subtitle: str
    domain: str
    sentiment: str
    
    # The 5 frames
    context: StoryFrame
    change: StoryFrame
    evidence: StoryFrame
    consequence: StoryFrame
    implication: StoryFrame
    
    # Metadata
    source_attribution: str
    time_period: str
    confidence: float
    
    def get_frames(self) -> List[StoryFrame]:
        return [self.context, self.change, self.evidence, 
                self.consequence, self.implication]
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "domain": self.domain,
            "sentiment": self.sentiment,
            "frames": [
                {
                    "type": f.frame_type,
                    "headline": f.headline,
                    "body_text": f.body_text,
                    "key_metric": f.key_metric,
                    "key_metric_label": f.key_metric_label,
                    "visual_hint": f.visual_hint,
                    "emphasis": f.emphasis
                }
                for f in self.get_frames()
            ],
            "source": self.source_attribution,
            "period": self.time_period,
            "confidence": self.confidence
        }


class NarrativeGenerator:
    """
    Generates compelling narratives from detected insights.
    
    Uses templates and rules to craft stories.
    Can be enhanced with Claude for more natural language.
    """
    
    # Frame templates by insight type
    TEMPLATES = {
        InsightType.GROWTH: {
            "context_headline": "Where We Started",
            "change_headline": "The Growth Story",
            "evidence_headline": "The Numbers Speak",
            "consequence_headline": "What This Means",
            "implication_headline": "Looking Ahead",
        },
        InsightType.DECLINE: {
            "context_headline": "The Starting Point",
            "change_headline": "The Decline",
            "evidence_headline": "The Evidence",
            "consequence_headline": "The Impact",
            "implication_headline": "Path Forward",
        },
        InsightType.COMPARISON: {
            "context_headline": "Two Stories",
            "change_headline": "The Divide",
            "evidence_headline": "By The Numbers",
            "consequence_headline": "Winners & Losers",
            "implication_headline": "Bridging The Gap",
        },
        InsightType.RANKING: {
            "context_headline": "The Field",
            "change_headline": "The Rankings",
            "evidence_headline": "Performance Data",
            "consequence_headline": "What Sets Them Apart",
            "implication_headline": "Lessons Learned",
        },
    }
    
    # Sentiment-based language
    SENTIMENT_LANGUAGE = {
        Sentiment.POSITIVE: {
            "tone": "optimistic",
            "verbs": ["achieved", "surpassed", "improved", "exceeded"],
            "adjectives": ["remarkable", "encouraging", "significant", "impressive"],
        },
        Sentiment.NEGATIVE: {
            "tone": "concerned",
            "verbs": ["declined", "dropped", "fell", "struggled"],
            "adjectives": ["concerning", "challenging", "troubling", "significant"],
        },
        Sentiment.NEUTRAL: {
            "tone": "objective",
            "verbs": ["changed", "shifted", "moved", "adjusted"],
            "adjectives": ["notable", "measurable", "observable", "clear"],
        },
        Sentiment.WARNING: {
            "tone": "cautionary",
            "verbs": ["signaled", "indicated", "revealed", "showed"],
            "adjectives": ["critical", "important", "urgent", "key"],
        },
    }
    
    def __init__(self, use_ai: bool = False, api_key: Optional[str] = None):
        self.use_ai = use_ai
        self.api_key = api_key
    
    def generate(
        self,
        insight: DetectedInsight,
        domain: str = "general",
        source: str = "Data Analysis",
        additional_context: Optional[str] = None
    ) -> Narrative:
        """
        Generate a 5-frame narrative from an insight.
        
        Args:
            insight: The detected insight
            domain: Domain for context (education, health, etc.)
            source: Data source attribution
            additional_context: Extra context to include
            
        Returns:
            Complete Narrative object
        """
        # Get templates for this insight type
        templates = self.TEMPLATES.get(
            insight.insight_type,
            self.TEMPLATES[InsightType.GROWTH]  # Default
        )
        
        # Get sentiment language
        lang = self.SENTIMENT_LANGUAGE.get(
            insight.sentiment,
            self.SENTIMENT_LANGUAGE[Sentiment.NEUTRAL]
        )
        
        # Generate each frame
        context_frame = self._generate_context(insight, templates, lang, domain)
        change_frame = self._generate_change(insight, templates, lang)
        evidence_frame = self._generate_evidence(insight, templates, lang)
        consequence_frame = self._generate_consequence(insight, templates, lang)
        implication_frame = self._generate_implication(insight, templates, lang)
        
        # Build title and subtitle
        title = self._generate_title(insight, lang)
        subtitle = self._generate_subtitle(insight, domain)
        
        # Time period
        if insight.time_range:
            time_period = f"{insight.time_range[0]} - {insight.time_range[1]}"
        else:
            time_period = "Recent Period"
        
        return Narrative(
            title=title,
            subtitle=subtitle,
            domain=domain,
            sentiment=insight.sentiment.value,
            context=context_frame,
            change=change_frame,
            evidence=evidence_frame,
            consequence=consequence_frame,
            implication=implication_frame,
            source_attribution=source,
            time_period=time_period,
            confidence=insight.confidence
        )
    
    def _generate_context(
        self,
        insight: DetectedInsight,
        templates: Dict,
        lang: Dict,
        domain: str
    ) -> StoryFrame:
        """Generate the Context frame - sets the stage"""
        headline = templates["context_headline"]
        
        metric_clean = insight.metric_name.replace('_', ' ').title()
        
        if insight.previous_value is not None:
            body = f"In {domain}, {metric_clean} stood at {insight.previous_value:.1f}. This baseline set the stage for what was to come."
            key_metric = f"{insight.previous_value:.1f}"
            metric_label = f"Starting {metric_clean}"
        else:
            body = f"Understanding {metric_clean} in {domain} requires looking at where things began."
            key_metric = None
            metric_label = ""
        
        return StoryFrame(
            frame_type="context",
            headline=headline,
            body_text=body,
            key_metric=key_metric,
            key_metric_label=metric_label,
            visual_hint="baseline_indicator",
            emphasis="starting_point"
        )
    
    def _generate_change(
        self,
        insight: DetectedInsight,
        templates: Dict,
        lang: Dict
    ) -> StoryFrame:
        """Generate the Change frame - what happened"""
        headline = templates["change_headline"]
        
        metric_clean = insight.metric_name.replace('_', ' ').title()
        verb = lang["verbs"][0]
        adj = lang["adjectives"][0]
        
        if insight.change_percentage is not None:
            direction = "increased" if insight.direction == "up" else "decreased"
            body = f"{metric_clean} {direction} by a {adj} {abs(insight.change_percentage):.1f}%. This {insight.magnitude} shift {verb} expectations."
            key_metric = f"{insight.change_percentage:+.1f}%"
            metric_label = "Change"
        else:
            body = f"A {adj} transformation occurred in {metric_clean}."
            key_metric = None
            metric_label = ""
        
        return StoryFrame(
            frame_type="change",
            headline=headline,
            body_text=body,
            key_metric=key_metric,
            key_metric_label=metric_label,
            visual_hint="trend_arrow",
            emphasis="change_magnitude"
        )
    
    def _generate_evidence(
        self,
        insight: DetectedInsight,
        templates: Dict,
        lang: Dict
    ) -> StoryFrame:
        """Generate the Evidence frame - proof"""
        headline = templates["evidence_headline"]
        
        metric_clean = insight.metric_name.replace('_', ' ').title()
        
        # Build evidence from data points
        num_points = len(insight.data_points) if insight.data_points else 0
        
        body = f"Based on {num_points} data points, {metric_clean} moved from {insight.previous_value:.1f} to {insight.current_value:.1f}."
        
        if insight.velocity:
            body += f" The change was {insight.velocity}."
        
        return StoryFrame(
            frame_type="evidence",
            headline=headline,
            body_text=body,
            key_metric=f"{insight.current_value:.1f}",
            key_metric_label=f"Current {metric_clean}",
            visual_hint="data_chart",
            emphasis="data_points"
        )
    
    def _generate_consequence(
        self,
        insight: DetectedInsight,
        templates: Dict,
        lang: Dict
    ) -> StoryFrame:
        """Generate the Consequence frame - impact"""
        headline = templates["consequence_headline"]
        
        body = insight.human_impact if insight.human_impact else f"This change has real implications for stakeholders."
        
        # Add sentiment-based framing
        if insight.sentiment == Sentiment.POSITIVE:
            body += " This represents progress worth celebrating."
        elif insight.sentiment == Sentiment.NEGATIVE:
            body += " This trend requires attention and action."
        elif insight.sentiment == Sentiment.WARNING:
            body += " Stakeholders should take note of this development."
        
        return StoryFrame(
            frame_type="consequence",
            headline=headline,
            body_text=body,
            key_metric=None,
            key_metric_label="",
            visual_hint="impact_icon",
            emphasis="human_element"
        )
    
    def _generate_implication(
        self,
        insight: DetectedInsight,
        templates: Dict,
        lang: Dict
    ) -> StoryFrame:
        """Generate the Implication frame - what's next"""
        headline = templates["implication_headline"]
        
        metric_clean = insight.metric_name.replace('_', ' ').title()
        
        if insight.direction == "up" and insight.sentiment == Sentiment.POSITIVE:
            body = f"If current trends continue, {metric_clean} could reach new heights. Sustained effort will be key."
        elif insight.direction == "down" and insight.sentiment == Sentiment.NEGATIVE:
            body = f"Reversing this trend in {metric_clean} will require focused intervention and resources."
        elif insight.direction == "up" and insight.sentiment == Sentiment.NEGATIVE:
            body = f"Addressing the rise in {metric_clean} should be a priority for policymakers."
        else:
            body = f"Monitoring {metric_clean} will be important to understand emerging patterns."
        
        return StoryFrame(
            frame_type="implication",
            headline=headline,
            body_text=body,
            key_metric=None,
            key_metric_label="",
            visual_hint="forward_arrow",
            emphasis="call_to_action"
        )
    
    def _generate_title(self, insight: DetectedInsight, lang: Dict) -> str:
        """Generate the main title"""
        metric_clean = insight.metric_name.replace('_', ' ').title()
        adj = lang["adjectives"][1]  # Second adjective for variety
        
        if insight.insight_type == InsightType.GROWTH:
            return f"{metric_clean} Shows {adj.title()} Growth"
        elif insight.insight_type == InsightType.DECLINE:
            return f"{metric_clean} Faces {adj.title()} Decline"
        elif insight.insight_type == InsightType.RANKING:
            return f"The {metric_clean} Rankings"
        elif insight.insight_type == InsightType.COMPARISON:
            return f"{metric_clean}: A Tale of Two Trends"
        else:
            return f"{metric_clean}: Key Insights"
    
    def _generate_subtitle(self, insight: DetectedInsight, domain: str) -> str:
        """Generate the subtitle"""
        if insight.time_range:
            return f"A {domain.title()} story from {insight.time_range[0]} to {insight.time_range[1]}"
        return f"Insights from {domain.title()} data"


def generate_narrative(
    insight: DetectedInsight,
    domain: str = "general",
    source: str = "Data Analysis"
) -> Narrative:
    """Quick function to generate narrative"""
    generator = NarrativeGenerator()
    return generator.generate(insight, domain, source)
