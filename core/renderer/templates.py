"""
Template Renderers
==================
Specific templates for different infographic types.
Each template combines layout, charts, text, and branding.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import io

from .base import BaseRenderer, RenderSpec, RenderOutput, TemplateRegistry
from .charts import ChartGenerator, get_chart_generator

logger = logging.getLogger(__name__)

# Try imports
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed - template rendering limited")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class HeroStatRenderer(BaseRenderer):
    """
    Hero Stat Template
    ------------------
    Large central number with supporting context.
    Best for: Single key metric, current state, thresholds
    """
    
    def render(self, spec: RenderSpec) -> RenderOutput:
        """Render hero stat infographic"""
        import time
        start = time.time()
        
        if not PIL_AVAILABLE:
            return RenderOutput(success=False, error_message="Pillow not installed")
        
        try:
            # Get colors
            colors = self.get_colors(spec.domain, spec.sentiment)
            
            # Create canvas
            width, height = self.SINGLE_WIDTH, self.SINGLE_HEIGHT
            img = Image.new('RGB', (width, height), colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Load fonts (use default if custom not available)
            try:
                font_hero = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                font_hero = font_title = font_subtitle = font_body = font_small = ImageFont.load_default()
            
            # Draw header section
            header_y = int(height * 0.08)
            draw.text((width//2, header_y), spec.title, fill=colors['text'], 
                     font=font_title, anchor="mt")
            
            if spec.subtitle:
                draw.text((width//2, header_y + 50), spec.subtitle, 
                         fill=colors['text_secondary'], font=font_subtitle, anchor="mt")
            
            # Draw hero number
            hero_y = int(height * 0.35)
            if spec.metrics:
                metric = spec.metrics[0]
                value = metric.get('value', 0)
                unit = metric.get('unit', '')
                label = metric.get('label', '')
                change = metric.get('change')
                
                # Format value
                if isinstance(value, float):
                    value_str = f"{value:.1f}{unit}"
                else:
                    value_str = f"{value}{unit}"
                
                # Draw value
                draw.text((width//2, hero_y), value_str, fill=colors['primary'],
                         font=font_hero, anchor="mm")
                
                # Draw label
                draw.text((width//2, hero_y + 100), label.replace('_', ' ').title(),
                         fill=colors['text_secondary'], font=font_subtitle, anchor="mt")
                
                # Draw change indicator
                if change is not None:
                    change_color = "#10B981" if change >= 0 else "#EF4444"
                    arrow = "▲" if change >= 0 else "▼"
                    draw.text((width//2, hero_y + 150), f"{arrow} {abs(change):.1f}%",
                             fill=change_color, font=font_subtitle, anchor="mt")
            
            # Draw insights section
            insight_y = int(height * 0.65)
            if spec.insights:
                for i, insight in enumerate(spec.insights[:3]):
                    y_pos = insight_y + (i * 40)
                    # Draw bullet
                    draw.ellipse([(80, y_pos-5), (90, y_pos+5)], fill=colors['primary'])
                    draw.text((110, y_pos), insight[:80], fill=colors['text'], 
                             font=font_body, anchor="lm")
            
            # Draw footer
            footer_y = int(height * 0.92)
            self._draw_footer(draw, width, footer_y, spec, colors, font_small)
            
            # Convert to bytes
            buf = io.BytesIO()
            img.save(buf, format='PNG', quality=95)
            buf.seek(0)
            
            render_time = (time.time() - start) * 1000
            
            return RenderOutput(
                success=True,
                image_bytes=buf.read(),
                format="png",
                width=width,
                height=height,
                render_time_ms=render_time,
                template_used="hero_stat"
            )
            
        except Exception as e:
            logger.error(f"Hero stat render failed: {e}", exc_info=True)
            return RenderOutput(success=False, error_message=str(e))
    
    def _draw_footer(self, draw, width, y, spec, colors, font):
        """Draw attribution footer"""
        if spec.source:
            draw.text((80, y), f"Source: {spec.source}", fill=colors['text_secondary'], 
                     font=font, anchor="lm")
        
        if spec.time_period:
            draw.text((width - 80, y), spec.time_period, fill=colors['text_secondary'],
                     font=font, anchor="rm")
        
        if spec.show_branding:
            draw.text((width//2, y + 30), "DataNarrative", fill=colors['text_secondary'],
                     font=font, anchor="mt")


class TrendLineRenderer(BaseRenderer):
    """
    Trend Line Template
    -------------------
    Line chart showing change over time.
    Best for: Growth, decline, time series
    """
    
    def render(self, spec: RenderSpec) -> RenderOutput:
        """Render trend line infographic"""
        import time
        start = time.time()
        
        if not PIL_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            return RenderOutput(success=False, error_message="Required libraries not installed")
        
        try:
            colors = self.get_colors(spec.domain, spec.sentiment)
            chart_gen = get_chart_generator()
            
            width, height = self.SINGLE_WIDTH, self.SINGLE_HEIGHT
            img = Image.new('RGB', (width, height), colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Load fonts
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                font_title = font_subtitle = font_small = ImageFont.load_default()
            
            # Draw header
            header_y = int(height * 0.06)
            draw.text((width//2, header_y), spec.title, fill=colors['text'],
                     font=font_title, anchor="mt")
            if spec.subtitle:
                draw.text((width//2, header_y + 45), spec.subtitle,
                         fill=colors['text_secondary'], font=font_subtitle, anchor="mt")
            
            # Generate chart
            if spec.chart_data:
                chart_bytes = chart_gen.create_line_chart(
                    spec.chart_data,
                    colors=colors,
                    title=None,
                    figsize=(9, 5)
                )
                
                if chart_bytes:
                    chart_img = Image.open(io.BytesIO(chart_bytes))
                    # Resize to fit
                    chart_width = int(width * 0.85)
                    chart_height = int(height * 0.45)
                    chart_img = chart_img.resize((chart_width, chart_height), Image.Resampling.LANCZOS)
                    # Paste chart
                    chart_x = (width - chart_width) // 2
                    chart_y = int(height * 0.18)
                    img.paste(chart_img, (chart_x, chart_y))
            
            # Draw key metrics
            metrics_y = int(height * 0.68)
            if spec.metrics:
                num_metrics = min(len(spec.metrics), 3)
                metric_width = width // (num_metrics + 1)
                
                for i, metric in enumerate(spec.metrics[:3]):
                    x_pos = metric_width * (i + 1)
                    value = metric.get('value', 0)
                    label = metric.get('label', '').replace('_', ' ').title()
                    
                    value_str = f"{value:.1f}" if isinstance(value, float) else str(value)
                    draw.text((x_pos, metrics_y), value_str, fill=colors['primary'],
                             font=font_title, anchor="mt")
                    draw.text((x_pos, metrics_y + 45), label, fill=colors['text_secondary'],
                             font=font_small, anchor="mt")
            
            # Draw insights
            insight_y = int(height * 0.82)
            if spec.insights:
                insight_text = spec.insights[0][:120] if spec.insights else ""
                draw.text((width//2, insight_y), insight_text, fill=colors['text'],
                         font=font_subtitle, anchor="mt")
            
            # Draw footer
            footer_y = int(height * 0.93)
            self._draw_footer(draw, width, footer_y, spec, colors, font_small)
            
            # Convert to bytes
            buf = io.BytesIO()
            img.save(buf, format='PNG', quality=95)
            buf.seek(0)
            
            render_time = (time.time() - start) * 1000
            
            return RenderOutput(
                success=True,
                image_bytes=buf.read(),
                format="png",
                width=width,
                height=height,
                render_time_ms=render_time,
                template_used="trend_line"
            )
            
        except Exception as e:
            logger.error(f"Trend line render failed: {e}", exc_info=True)
            return RenderOutput(success=False, error_message=str(e))
    
    def _draw_footer(self, draw, width, y, spec, colors, font):
        """Draw footer"""
        if spec.source:
            draw.text((80, y), f"Source: {spec.source}", fill=colors['text_secondary'], font=font)
        if spec.show_branding:
            draw.text((width - 80, y), "DataNarrative", fill=colors['text_secondary'], 
                     font=font, anchor="rm")


class RankingBarRenderer(BaseRenderer):
    """
    Ranking Bar Template
    --------------------
    Horizontal bar chart for rankings.
    Best for: Top/bottom lists, comparisons
    """
    
    def render(self, spec: RenderSpec) -> RenderOutput:
        """Render ranking bar infographic"""
        import time
        start = time.time()
        
        if not PIL_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            return RenderOutput(success=False, error_message="Required libraries not installed")
        
        try:
            colors = self.get_colors(spec.domain, spec.sentiment)
            chart_gen = get_chart_generator()
            
            width, height = self.SINGLE_WIDTH, self.SINGLE_HEIGHT
            img = Image.new('RGB', (width, height), colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Load fonts
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                font_title = font_subtitle = font_small = ImageFont.load_default()
            
            # Draw header
            header_y = int(height * 0.06)
            draw.text((width//2, header_y), spec.title, fill=colors['text'],
                     font=font_title, anchor="mt")
            if spec.subtitle:
                draw.text((width//2, header_y + 45), spec.subtitle,
                         fill=colors['text_secondary'], font=font_subtitle, anchor="mt")
            
            # Generate horizontal bar chart
            if spec.chart_data:
                chart_bytes = chart_gen.create_bar_chart(
                    spec.chart_data,
                    colors=colors,
                    title=None,
                    figsize=(9, 7),
                    horizontal=True
                )
                
                if chart_bytes:
                    chart_img = Image.open(io.BytesIO(chart_bytes))
                    chart_width = int(width * 0.85)
                    chart_height = int(height * 0.55)
                    chart_img = chart_img.resize((chart_width, chart_height), Image.Resampling.LANCZOS)
                    chart_x = (width - chart_width) // 2
                    chart_y = int(height * 0.16)
                    img.paste(chart_img, (chart_x, chart_y))
            
            # Draw insight
            insight_y = int(height * 0.78)
            if spec.insights:
                insight_text = spec.insights[0][:120] if spec.insights else ""
                draw.text((width//2, insight_y), insight_text, fill=colors['text'],
                         font=font_subtitle, anchor="mt")
            
            # Draw footer
            footer_y = int(height * 0.93)
            if spec.source:
                draw.text((80, footer_y), f"Source: {spec.source}", fill=colors['text_secondary'], font=font_small)
            if spec.show_branding:
                draw.text((width - 80, footer_y), "DataNarrative", fill=colors['text_secondary'],
                         font=font_small, anchor="rm")
            
            # Convert to bytes
            buf = io.BytesIO()
            img.save(buf, format='PNG', quality=95)
            buf.seek(0)
            
            render_time = (time.time() - start) * 1000
            
            return RenderOutput(
                success=True,
                image_bytes=buf.read(),
                format="png",
                width=width,
                height=height,
                render_time_ms=render_time,
                template_used="ranking_bar"
            )
            
        except Exception as e:
            logger.error(f"Ranking bar render failed: {e}", exc_info=True)
            return RenderOutput(success=False, error_message=str(e))


class VersusRenderer(BaseRenderer):
    """
    Versus Template
    ---------------
    Side-by-side comparison of two items.
    Best for: Before/after, A vs B comparisons
    """
    
    def render(self, spec: RenderSpec) -> RenderOutput:
        """Render versus comparison infographic"""
        import time
        start = time.time()
        
        if not PIL_AVAILABLE:
            return RenderOutput(success=False, error_message="Pillow not installed")
        
        try:
            colors = self.get_colors(spec.domain, spec.sentiment)
            
            width, height = self.SINGLE_WIDTH, self.SINGLE_HEIGHT
            img = Image.new('RGB', (width, height), colors['background'])
            draw = ImageDraw.Draw(img)
            
            # Load fonts
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                font_hero = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
                font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                font_title = font_hero = font_label = font_small = ImageFont.load_default()
            
            # Draw header
            header_y = int(height * 0.06)
            draw.text((width//2, header_y), spec.title, fill=colors['text'],
                     font=font_title, anchor="mt")
            
            # Draw VS divider
            center_y = int(height * 0.45)
            draw.text((width//2, center_y), "VS", fill=colors['text_secondary'],
                     font=font_title, anchor="mm")
            
            # Draw comparison items
            if len(spec.metrics) >= 2:
                left_metric = spec.metrics[0]
                right_metric = spec.metrics[1]
                
                left_x = width // 4
                right_x = width * 3 // 4
                
                # Left side
                left_val = left_metric.get('value', 0)
                left_label = left_metric.get('label', 'Before')
                val_str = f"{left_val:.1f}" if isinstance(left_val, float) else str(left_val)
                draw.text((left_x, center_y - 80), val_str, fill=colors['secondary'],
                         font=font_hero, anchor="mm")
                draw.text((left_x, center_y + 40), left_label, fill=colors['text_secondary'],
                         font=font_label, anchor="mm")
                
                # Right side  
                right_val = right_metric.get('value', 0)
                right_label = right_metric.get('label', 'After')
                val_str = f"{right_val:.1f}" if isinstance(right_val, float) else str(right_val)
                draw.text((right_x, center_y - 80), val_str, fill=colors['primary'],
                         font=font_hero, anchor="mm")
                draw.text((right_x, center_y + 40), right_label, fill=colors['text_secondary'],
                         font=font_label, anchor="mm")
                
                # Draw change arrow
                if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                    change = ((right_val - left_val) / left_val) * 100 if left_val != 0 else 0
                    change_color = "#10B981" if change >= 0 else "#EF4444"
                    arrow = "▲" if change >= 0 else "▼"
                    draw.text((width//2, center_y + 120), f"{arrow} {abs(change):.1f}%",
                             fill=change_color, font=font_title, anchor="mt")
            
            # Draw insight
            insight_y = int(height * 0.75)
            if spec.insights:
                draw.text((width//2, insight_y), spec.insights[0][:100],
                         fill=colors['text'], font=font_label, anchor="mt")
            
            # Draw footer
            footer_y = int(height * 0.93)
            if spec.source:
                draw.text((80, footer_y), f"Source: {spec.source}", fill=colors['text_secondary'], font=font_small)
            if spec.show_branding:
                draw.text((width - 80, footer_y), "DataNarrative", fill=colors['text_secondary'],
                         font=font_small, anchor="rm")
            
            buf = io.BytesIO()
            img.save(buf, format='PNG', quality=95)
            buf.seek(0)
            
            render_time = (time.time() - start) * 1000
            
            return RenderOutput(
                success=True,
                image_bytes=buf.read(),
                format="png",
                width=width,
                height=height,
                render_time_ms=render_time,
                template_used="versus"
            )
            
        except Exception as e:
            logger.error(f"Versus render failed: {e}", exc_info=True)
            return RenderOutput(success=False, error_message=str(e))


# Register templates
TemplateRegistry.register("hero_stat", HeroStatRenderer)
TemplateRegistry.register("trend_line", TrendLineRenderer)
TemplateRegistry.register("ranking_bar", RankingBarRenderer)
TemplateRegistry.register("versus", VersusRenderer)
