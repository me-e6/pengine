"""
Intelligence Module
===================
The brain of DataNarrative.

Components:
- Analyzer: Query understanding
- Detector: Insight detection
- Narrator: Story generation
- Reasoning: Main orchestrator
"""

from .analyzer import (
    QueryAnalyzer,
    QueryAnalysis,
    QueryIntent,
    analyze_query,
)

from .detector import (
    InsightDetector,
    DetectedInsight,
    InsightType,
    Sentiment,
    detect_insights,
)

from .narrator import (
    NarrativeGenerator,
    Narrative,
    StoryFrame,
    generate_narrative,
)

from .reasoning import (
    ReasoningEngine,
    ReasoningResult,
    reason_query,
)

__all__ = [
    # Analyzer
    "QueryAnalyzer",
    "QueryAnalysis",
    "QueryIntent",
    "analyze_query",
    
    # Detector
    "InsightDetector",
    "DetectedInsight",
    "InsightType",
    "Sentiment",
    "detect_insights",
    
    # Narrator
    "NarrativeGenerator",
    "Narrative",
    "StoryFrame",
    "generate_narrative",
    
    # Reasoning
    "ReasoningEngine",
    "ReasoningResult",
    "reason_query",
]
