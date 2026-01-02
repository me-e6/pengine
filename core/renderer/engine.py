"""
Render Engine
=============
Main orchestrator for all rendering operations.
Selects appropriate template and coordinates rendering.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import time

from .base import BaseRenderer, RenderSpec, RenderOutput, TemplateRegistry
from .charts import ChartGenerator, get_chart_generator

logger = logging.getLogger(__name__)


class RenderEngine:
    """
    Main rendering engine.
    
    Coordinates:
    - Template selection
    - Chart generation
    - Final composition
    - Output saving
    
    Usage:
        engine = RenderEngine()
        
        spec = RenderSpec(
            title="Literacy in Telangana",
            template_type="trend_line",
            chart_data=[...],
            metrics=[...]
        )
        
        result = engine.render(spec)
        path = engine.save(result, "literacy_trend.png")
    """
    
    def __init__(self, output_dir: str = "./storage/outputs"):
        """
        Initialize render engine.
        
        Args:
            output_dir: Directory for saving outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chart_generator = get_chart_generator()
        
        # Import templates to register them
        from . import templates
        from . import story
    
    def render(self, spec: RenderSpec) -> RenderOutput:
        """
        Render an infographic from specification.
        
        Automatically selects the appropriate renderer based on
        spec.template_type and spec.output_mode.
        
        Args:
            spec: Complete render specification
            
        Returns:
            RenderOutput with image bytes
        """
        logger.info(f"Rendering: template={spec.template_type}, mode={spec.output_mode}")
        
        # Determine template to use
        if spec.output_mode == "story":
            template_name = "story_five_frame" if spec.story_format != "carousel" else "story_carousel"
        else:
            template_name = spec.template_type
        
        # Get renderer class
        renderer_class = TemplateRegistry.get(template_name)
        
        if not renderer_class:
            # Fallback to hero_stat
            logger.warning(f"Template '{template_name}' not found, using hero_stat")
            renderer_class = TemplateRegistry.get("hero_stat")
        
        if not renderer_class:
            return RenderOutput(
                success=False,
                error_message=f"No renderer available for template: {template_name}"
            )
        
        # Create renderer instance
        renderer = renderer_class(output_dir=str(self.output_dir))
        
        # Render
        result = renderer.render(spec)
        
        logger.info(f"Render complete: success={result.success}, time={result.render_time_ms:.1f}ms")
        
        return result
    
    def render_from_reasoning(self, reasoning_result) -> RenderOutput:
        """
        Render from a ReasoningResult object.
        
        Converts reasoning output to RenderSpec and renders.
        
        Args:
            reasoning_result: Output from ReasoningEngine
            
        Returns:
            RenderOutput
        """
        # Build RenderSpec from reasoning result
        spec = RenderSpec(
            output_mode=reasoning_result.output_mode,
            template_type=reasoning_result.recommended_template,
            title=reasoning_result.render_data.get('title', reasoning_result.query),
            subtitle=reasoning_result.render_data.get('subtitle', ''),
            metrics=reasoning_result.render_data.get('metrics', []),
            chart_data=reasoning_result.render_data.get('chart_data', []),
            insights=[i.get('summary', '') for i in reasoning_result.render_data.get('insights', [])],
            narrative_frames=reasoning_result.render_data.get('narrative_frames', []),
            domain=reasoning_result.query_analysis.domain_hint or 'general',
            source=', '.join(reasoning_result.sources_used[:2]) if reasoning_result.sources_used else '',
        )
        
        # Add narrative if in story mode
        if reasoning_result.narrative:
            spec.narrative_frames = reasoning_result.narrative.to_dict().get('frames', [])
        
        return self.render(spec)
    
    def render_quick(
        self,
        title: str,
        value: Any,
        label: str,
        change: Optional[float] = None,
        domain: str = "general",
        template: str = "hero_stat"
    ) -> RenderOutput:
        """
        Quick render for simple single-metric infographics.
        
        Args:
            title: Main title
            value: Hero value
            label: Value label
            change: Percentage change
            domain: Domain for colors
            template: Template to use
            
        Returns:
            RenderOutput
        """
        spec = RenderSpec(
            template_type=template,
            title=title,
            metrics=[{
                "value": value,
                "label": label,
                "change": change
            }],
            domain=domain
        )
        
        return self.render(spec)
    
    def save(
        self,
        output: RenderOutput,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Save render output to file.
        
        Args:
            output: RenderOutput to save
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file, or None if failed
        """
        if not output.success or not output.image_bytes:
            logger.error("Cannot save failed render output")
            return None
        
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"infogram_{timestamp}.{output.format}"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'wb') as f:
                f.write(output.image_bytes)
            
            output.image_path = str(filepath)
            logger.info(f"Saved render to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save render: {e}")
            return None
    
    def save_carousel(
        self,
        output: RenderOutput,
        prefix: str = "story"
    ) -> List[str]:
        """
        Save carousel images (multiple files).
        
        Args:
            output: RenderOutput with images list
            prefix: Filename prefix
            
        Returns:
            List of saved file paths
        """
        if not output.success or not output.images:
            logger.error("Cannot save carousel - no images")
            return []
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        paths = []
        
        for i, img_bytes in enumerate(output.images):
            filename = f"{prefix}_{timestamp}_{i+1}.{output.format}"
            filepath = self.output_dir / filename
            
            try:
                with open(filepath, 'wb') as f:
                    f.write(img_bytes)
                paths.append(str(filepath))
            except Exception as e:
                logger.error(f"Failed to save carousel image {i+1}: {e}")
        
        logger.info(f"Saved {len(paths)} carousel images")
        return paths
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        List all available templates.
        
        Returns:
            List of template info dicts
        """
        templates = TemplateRegistry.list_templates()
        
        template_info = {
            "hero_stat": {
                "name": "Hero Stat",
                "description": "Large central number with supporting context",
                "best_for": ["Single key metric", "Current state", "Thresholds"]
            },
            "trend_line": {
                "name": "Trend Line",
                "description": "Line chart showing change over time",
                "best_for": ["Growth trends", "Time series", "Historical data"]
            },
            "ranking_bar": {
                "name": "Ranking Bar",
                "description": "Horizontal bar chart for rankings",
                "best_for": ["Top/bottom lists", "Comparisons", "League tables"]
            },
            "versus": {
                "name": "Versus",
                "description": "Side-by-side comparison of two items",
                "best_for": ["Before/after", "A vs B", "Two-way comparison"]
            },
            "story_five_frame": {
                "name": "Story (5 Frame)",
                "description": "5-frame narrative with context, change, evidence, consequence, implication",
                "best_for": ["Trend stories", "Data narratives", "Comprehensive analysis"]
            },
            "story_carousel": {
                "name": "Story Carousel",
                "description": "5 separate images for social media carousel",
                "best_for": ["Instagram carousel", "Social media", "Slide decks"]
            }
        }
        
        return [
            {
                "id": t,
                **template_info.get(t, {"name": t, "description": "", "best_for": []})
            }
            for t in templates
        ]


# Global instance
_engine: Optional[RenderEngine] = None


def get_render_engine(output_dir: str = "./storage/outputs") -> RenderEngine:
    """Get or create render engine instance"""
    global _engine
    if _engine is None:
        _engine = RenderEngine(output_dir=output_dir)
    return _engine


def render_infogram(spec: RenderSpec) -> RenderOutput:
    """Quick render function"""
    engine = get_render_engine()
    return engine.render(spec)
