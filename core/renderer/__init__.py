"""
Renderer Module
===============
Visual output generation for DataNarrative.

Components:
- Base: Foundation classes and interfaces
- Charts: Matplotlib-based chart generation
- Templates: Specific template renderers
- Story: 5-frame narrative renderer
- Engine: Main orchestrator
"""

from .base import (
    BaseRenderer,
    RenderSpec,
    RenderOutput,
    TemplateRegistry,
)

from .charts import (
    ChartGenerator,
    get_chart_generator,
)

from .templates import (
    HeroStatRenderer,
    TrendLineRenderer,
    RankingBarRenderer,
    VersusRenderer,
)

from .story import (
    StoryRenderer,
)

from .engine import (
    RenderEngine,
    get_render_engine,
    render_infogram,
)

__all__ = [
    # Base
    "BaseRenderer",
    "RenderSpec",
    "RenderOutput",
    "TemplateRegistry",
    
    # Charts
    "ChartGenerator",
    "get_chart_generator",
    
    # Templates
    "HeroStatRenderer",
    "TrendLineRenderer",
    "RankingBarRenderer",
    "VersusRenderer",
    "StoryRenderer",
    
    # Engine
    "RenderEngine",
    "get_render_engine",
    "render_infogram",
]
