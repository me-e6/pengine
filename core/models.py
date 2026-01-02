"""
DataNarrative Core Models
=========================
Central data structures used throughout the platform.
These models define the shape of data as it flows through the system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid


# ============================================================================
# ENUMS - Fixed categories
# ============================================================================

class Domain(str, Enum):
    """Data domain categories"""
    EDUCATION = "education"
    AGRICULTURE = "agriculture"
    ECONOMY = "economy"
    HEALTH = "health"
    INFRASTRUCTURE = "infrastructure"
    ENVIRONMENT = "environment"
    DEMOGRAPHICS = "demographics"
    LAW = "law"
    OTHER = "other"


class InsightType(str, Enum):
    """Types of insights the system can detect"""
    GROWTH = "growth"
    DECLINE = "decline"
    COMPARISON = "comparison"
    RANKING = "ranking"
    DISTRIBUTION = "distribution"
    CORRELATION = "correlation"
    ANOMALY = "anomaly"
    THRESHOLD = "threshold"
    STABILITY = "stability"


class Sentiment(str, Enum):
    """Emotional tone of the insight"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    WARNING = "warning"


class OutputMode(str, Enum):
    """How the infogram should be generated"""
    STORY = "story"      # 5-frame narrative
    DATA = "data"        # Single infographic


class StoryFormat(str, Enum):
    """Story mode output format"""
    SINGLE = "single"      # All 5 panels in one image
    CAROUSEL = "carousel"  # 5 separate images


class TemplateType(str, Enum):
    """Available template types"""
    HERO_STAT = "hero_stat"
    BEFORE_AFTER = "before_after"
    RANKING_BAR = "ranking_bar"
    TREND_LINE = "trend_line"
    PIE_BREAKDOWN = "pie_breakdown"
    VERSUS = "versus"
    STORY_FIVE_FRAME = "story_five_frame"


class ApprovalStatus(str, Enum):
    """Status of generated content"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============================================================================
# DATA CHUNKS - How data is stored in knowledge base
# ============================================================================

@dataclass
class DataChunk:
    """
    A single piece of knowledge stored in the system.
    This is the atomic unit of the knowledge base.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Content
    content: str = ""
    content_type: str = "text"  # text, table, metric
    
    # Source tracking
    source_file: str = ""
    source_name: str = ""       # "RBI", "Census", etc.
    source_url: Optional[str] = None
    
    # Context
    domain: Domain = Domain.OTHER
    year: Optional[int] = None
    year_range: Optional[tuple] = None  # (start_year, end_year)
    region: Optional[str] = None
    entities: List[str] = field(default_factory=list)
    
    # For structured data
    columns: List[str] = field(default_factory=list)
    data_rows: List[Dict] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    has_historical_depth: bool = False  # Can support Story Mode
    
    def to_embedding_text(self) -> str:
        """Convert chunk to text for embedding generation"""
        parts = [self.content]
        if self.source_name:
            parts.append(f"Source: {self.source_name}")
        if self.domain != Domain.OTHER:
            parts.append(f"Domain: {self.domain.value}")
        if self.year:
            parts.append(f"Year: {self.year}")
        if self.year_range:
            parts.append(f"Period: {self.year_range[0]}-{self.year_range[1]}")
        if self.region:
            parts.append(f"Region: {self.region}")
        if self.entities:
            parts.append(f"Entities: {', '.join(self.entities[:5])}")
        return "\n".join(parts)


# ============================================================================
# INSIGHTS - What the intelligence layer produces
# ============================================================================

@dataclass
class Insight:
    """
    A meaningful pattern or finding detected in the data.
    This is what answers the Four Universal Questions.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Q1: What is the data really saying?
    summary: str = ""
    
    # Q2: What changed meaningfully?
    insight_type: InsightType = InsightType.COMPARISON
    change_description: str = ""
    magnitude: Optional[str] = None      # "42% increase"
    direction: Optional[str] = None      # "up", "down", "stable"
    velocity: Optional[str] = None       # "accelerating", "steady"
    
    # Q3: Why does it matter to humans?
    human_impact: str = ""
    affected_count: Optional[str] = None  # "2.3 million people"
    
    # Q4: How should this be shown?
    recommended_template: TemplateType = TemplateType.HERO_STAT
    sentiment: Sentiment = Sentiment.NEUTRAL
    
    # Supporting data
    evidence_chunks: List[str] = field(default_factory=list)  # Chunk IDs
    key_metrics: List[Dict] = field(default_factory=list)
    time_range: Optional[tuple] = None
    
    # Confidence
    confidence: float = 0.8
    uncertainty_flags: List[str] = field(default_factory=list)


# ============================================================================
# NARRATIVE - The story structure for Story Mode
# ============================================================================

@dataclass
class StoryFrame:
    """A single frame in the 5-frame narrative"""
    frame_number: int
    frame_type: str          # context, change, evidence, consequence, implication
    headline: str = ""
    body_text: str = ""
    key_metric: Optional[Dict] = None
    visual_type: Optional[str] = None
    visual_data: Optional[Dict] = None


@dataclass
class Narrative:
    """
    Complete story structure for Story Mode.
    Contains all 5 frames of the narrative.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Story metadata
    title: str = ""
    subtitle: str = ""
    domain: Domain = Domain.OTHER
    insight: Optional[Insight] = None
    
    # The 5 frames
    frames: List[StoryFrame] = field(default_factory=list)
    
    # Frame content helpers
    context: str = ""       # Frame 1: What was the baseline?
    change: str = ""        # Frame 2: What happened?
    evidence: str = ""      # Frame 3: How do we know?
    consequence: str = ""   # Frame 4: Why does it matter?
    implication: str = ""   # Frame 5: What now?
    
    def build_frames(self):
        """Construct the 5 frames from content"""
        self.frames = [
            StoryFrame(1, "context", "The Starting Point", self.context),
            StoryFrame(2, "change", "What Changed", self.change),
            StoryFrame(3, "evidence", "The Evidence", self.evidence),
            StoryFrame(4, "consequence", "Why It Matters", self.consequence),
            StoryFrame(5, "implication", "Looking Ahead", self.implication),
        ]


# ============================================================================
# RENDER SPECIFICATION - What goes to the renderer
# ============================================================================

@dataclass
class RenderSpec:
    """
    Complete specification for rendering an infogram.
    This is what the renderer uses to produce the final image.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Output settings
    output_mode: OutputMode = OutputMode.DATA
    story_format: StoryFormat = StoryFormat.SINGLE
    template_type: TemplateType = TemplateType.HERO_STAT
    
    # Content
    title: str = ""
    subtitle: str = ""
    
    # For Data Mode
    headline: str = ""
    primary_metric: Optional[Dict] = None    # {"value": "42%", "label": "Growth"}
    secondary_metrics: List[Dict] = field(default_factory=list)
    chart_data: Optional[Dict] = None
    key_insights: List[str] = field(default_factory=list)
    
    # For Story Mode
    narrative: Optional[Narrative] = None
    
    # Visual settings
    domain: Domain = Domain.OTHER
    sentiment: Sentiment = Sentiment.NEUTRAL
    color_override: Optional[str] = None
    
    # Source attribution
    source_text: str = ""
    data_date: str = ""
    
    # Branding
    include_watermark: bool = True


# ============================================================================
# API MODELS - Request/Response structures
# ============================================================================

@dataclass
class QueryRequest:
    """User query input"""
    query: str
    domain_hint: Optional[str] = None
    prefer_story_mode: bool = True
    story_format: StoryFormat = StoryFormat.SINGLE


@dataclass
class DataInputRequest:
    """User data upload input"""
    source_name: str
    file_type: str = "csv"
    domain_hint: Optional[str] = None
    description: Optional[str] = None


@dataclass
class GeneratedInfogram:
    """Output of the generation process"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Content
    render_spec: Optional[RenderSpec] = None
    insight: Optional[Insight] = None
    
    # Output
    output_mode: OutputMode = OutputMode.DATA
    image_paths: List[str] = field(default_factory=list)
    
    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    
    # Metadata
    query_used: Optional[str] = None
    source_chunks: List[str] = field(default_factory=list)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def detect_historical_depth(data: List[Dict], columns: List[str]) -> bool:
    """
    Check if data has enough historical depth for Story Mode.
    Returns True if data spans multiple time periods.
    """
    time_indicators = ['year', 'date', 'period', 'month', 'quarter', 'fy', 'fiscal']
    
    # Check if any column looks like a time column
    time_col = None
    for col in columns:
        if any(indicator in col.lower() for indicator in time_indicators):
            time_col = col
            break
    
    if not time_col:
        return False
    
    # Check if we have multiple time periods
    try:
        unique_periods = set(row.get(time_col) for row in data if row.get(time_col))
        return len(unique_periods) >= 3
    except:
        return False


def get_sentiment_from_insight(insight_type: InsightType, direction: str = None) -> Sentiment:
    """Determine sentiment based on insight type and direction"""
    if insight_type == InsightType.GROWTH:
        return Sentiment.POSITIVE
    elif insight_type == InsightType.DECLINE:
        return Sentiment.NEGATIVE
    elif insight_type in [InsightType.ANOMALY, InsightType.THRESHOLD]:
        return Sentiment.WARNING
    else:
        return Sentiment.NEUTRAL
