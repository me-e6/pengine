"""
Base Renderer
=============
Foundation for all rendering operations.
Defines common interfaces and utilities.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import io

logger = logging.getLogger(__name__)


@dataclass
class RenderSpec:
    """Complete specification for rendering an infographic"""
    # Output settings
    output_mode: str = "data"          # "story" or "data"
    template_type: str = "hero_stat"   # Template to use
    story_format: str = "single"       # "single" or "carousel" for story mode
    
    # Content
    title: str = ""
    subtitle: str = ""
    
    # Main metrics
    metrics: List[Dict] = field(default_factory=list)
    # Each metric: {"value": 89.5, "label": "Literacy Rate", "change": 7.6, "unit": "%"}
    
    # Chart data
    chart_data: List[Dict] = field(default_factory=list)
    chart_type: str = "bar"            # "bar", "line", "pie", "comparison"
    
    # Insights text
    insights: List[str] = field(default_factory=list)
    
    # Story frames (for story mode)
    narrative_frames: List[Dict] = field(default_factory=list)
    
    # Styling
    domain: str = "general"
    sentiment: str = "neutral"         # "positive", "negative", "neutral", "warning"
    color_scheme: Optional[str] = None
    
    # Attribution
    source: str = ""
    time_period: str = ""
    
    # Branding
    show_branding: bool = True
    show_watermark: bool = True


@dataclass 
class RenderOutput:
    """Result of rendering"""
    success: bool
    image_bytes: Optional[bytes] = None
    image_path: Optional[str] = None
    format: str = "png"
    width: int = 1080
    height: int = 1350
    
    # For carousel/multi-image
    images: List[bytes] = field(default_factory=list)
    
    # Metadata
    render_time_ms: float = 0
    template_used: str = ""
    error_message: Optional[str] = None


class BaseRenderer(ABC):
    """
    Abstract base class for all renderers.
    
    Subclasses implement specific template rendering.
    """
    
    # Standard dimensions
    SINGLE_WIDTH = 1080
    SINGLE_HEIGHT = 1350      # Instagram portrait
    STORY_WIDTH = 1080
    STORY_HEIGHT = 1920       # Instagram/mobile story
    
    # Standard margins (as percentage)
    MARGIN_TOP = 0.05
    MARGIN_BOTTOM = 0.08
    MARGIN_LEFT = 0.06
    MARGIN_RIGHT = 0.06
    
    def __init__(self, output_dir: str = "./storage/outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def render(self, spec: RenderSpec) -> RenderOutput:
        """
        Render an infographic from specification.
        
        Args:
            spec: Complete render specification
            
        Returns:
            RenderOutput with image bytes and metadata
        """
        pass
    
    def save(self, output: RenderOutput, filename: Optional[str] = None) -> str:
        """
        Save rendered output to file.
        
        Returns:
            Path to saved file
        """
        if not output.success or not output.image_bytes:
            raise ValueError("Cannot save failed render")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"infogram_{timestamp}.{output.format}"
        
        filepath = self.output_dir / filename
        
        with open(filepath, "wb") as f:
            f.write(output.image_bytes)
        
        output.image_path = str(filepath)
        return str(filepath)
    
    def get_colors(self, domain: str, sentiment: str) -> Dict[str, str]:
        """Get color palette for domain and sentiment"""
        # Import from config
        try:
            from config import DOMAIN_CONFIG, SENTIMENT_COLORS
            
            domain_colors = DOMAIN_CONFIG.get(domain, DOMAIN_CONFIG.get("other", {}))
            sentiment_palette = SENTIMENT_COLORS.get(sentiment, SENTIMENT_COLORS.get("neutral", {}))
            
            return {
                "primary": domain_colors.get("color_primary", "#3B82F6"),
                "secondary": domain_colors.get("color_secondary", "#93C5FD"),
                "accent": sentiment_palette.get("accent", "#10B981"),
                "background": sentiment_palette.get("background", "#F8FAFC"),
                "text": "#1E293B",
                "text_secondary": "#64748B",
                "highlight": sentiment_palette.get("highlight", "#FBBF24"),
            }
        except ImportError:
            # Fallback colors
            return {
                "primary": "#3B82F6",
                "secondary": "#93C5FD",
                "accent": "#10B981",
                "background": "#F8FAFC",
                "text": "#1E293B",
                "text_secondary": "#64748B",
                "highlight": "#FBBF24",
            }
    
    def get_fonts(self) -> Dict[str, str]:
        """Get font configuration"""
        return {
            "headline": "DejaVu Sans",    # Available on most systems
            "body": "DejaVu Sans",
            "numbers": "DejaVu Sans",
        }


class TemplateRegistry:
    """Registry of available templates"""
    
    _templates: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, renderer_class: type):
        """Register a template renderer"""
        cls._templates[name] = renderer_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """Get a template renderer by name"""
        return cls._templates.get(name)
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """List all registered templates"""
        return list(cls._templates.keys())
