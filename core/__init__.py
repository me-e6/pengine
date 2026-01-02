"""
DataNarrative Core
==================
The brain of the system.
"""

from .models import (
    # Enums
    Domain,
    InsightType,
    Sentiment,
    OutputMode,
    StoryFormat,
    TemplateType,
    ApprovalStatus,
    
    # Data structures
    DataChunk,
    Insight,
    StoryFrame,
    Narrative,
    RenderSpec,
    GeneratedInfogram,
    
    # Request/Response
    QueryRequest,
    DataInputRequest,
    
    # Helpers
    detect_historical_depth,
    get_sentiment_from_insight,
)

__all__ = [
    "Domain",
    "InsightType", 
    "Sentiment",
    "OutputMode",
    "StoryFormat",
    "TemplateType",
    "ApprovalStatus",
    "DataChunk",
    "Insight",
    "StoryFrame",
    "Narrative",
    "RenderSpec",
    "GeneratedInfogram",
    "QueryRequest",
    "DataInputRequest",
    "detect_historical_depth",
    "get_sentiment_from_insight",
]
