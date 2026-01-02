"""
Story Mode Renderer
===================
Renders 5-frame story narratives.
Creates either single combined image or carousel of separate images.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import io

from .base import BaseRenderer, RenderSpec, RenderOutput

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class StoryRenderer(BaseRenderer):
    """
    5-Frame Story Renderer
    ----------------------
    Creates visual narratives with:
    1. Context - Where we started
    2. Change - What happened
    3. Evidence - The proof
    4. Consequence - What it means
    5. Implication - What's next
    
    Can output as:
    - Single combined image (5 panels stacked)
    - Carousel of 5 separate images
    """
    
    # Frame colors by type
    FRAME_ACCENTS = {
        "context": "#64748B",      # Slate - neutral start
        "change": "#3B82F6",        # Blue - the shift
        "evidence": "#8B5CF6",      # Purple - data
        "consequence": "#F59E0B",   # Amber - impact
        "implication": "#10B981",   # Green - future
    }
    
    def render(self, spec: RenderSpec) -> RenderOutput:
        """
        Render story mode infographic.
        
        Creates either single image or carousel based on spec.story_format
        """
        import time
        start = time.time()
        
        if not PIL_AVAILABLE:
            return RenderOutput(success=False, error_message="Pillow not installed")
        
        try:
            if spec.story_format == "carousel":
                return self._render_carousel(spec, start)
            else:
                return self._render_single(spec, start)
                
        except Exception as e:
            logger.error(f"Story render failed: {e}", exc_info=True)
            return RenderOutput(success=False, error_message=str(e))
    
    def _render_single(self, spec: RenderSpec, start_time: float) -> RenderOutput:
        """Render as single combined image with 5 panels"""
        import time
        
        colors = self.get_colors(spec.domain, spec.sentiment)
        
        width = self.STORY_WIDTH
        height = self.STORY_HEIGHT
        
        img = Image.new('RGB', (width, height), colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            font_headline = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_metric = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_title = font_headline = font_body = font_metric = font_small = ImageFont.load_default()
        
        # Draw main title at top
        title_y = 40
        draw.text((width//2, title_y), spec.title, fill=colors['text'],
                 font=font_title, anchor="mt")
        if spec.subtitle:
            draw.text((width//2, title_y + 35), spec.subtitle,
                     fill=colors['text_secondary'], font=font_body, anchor="mt")
        
        # Calculate frame positions
        frames = spec.narrative_frames or []
        num_frames = min(len(frames), 5)
        
        if num_frames == 0:
            # No frames - show placeholder
            draw.text((width//2, height//2), "No story data available",
                     fill=colors['text_secondary'], font=font_headline, anchor="mm")
        else:
            # Frame heights
            content_start = 100
            content_height = height - 180  # Leave space for header and footer
            frame_height = content_height // num_frames
            
            for i, frame in enumerate(frames[:5]):
                frame_y = content_start + (i * frame_height)
                frame_type = frame.get('type', 'context')
                accent_color = self.FRAME_ACCENTS.get(frame_type, colors['primary'])
                
                self._draw_frame(
                    draw, 
                    frame,
                    x=40,
                    y=frame_y,
                    width=width - 80,
                    height=frame_height - 10,
                    accent_color=accent_color,
                    fonts={
                        'headline': font_headline,
                        'body': font_body,
                        'metric': font_metric,
                        'small': font_small
                    },
                    colors=colors
                )
        
        # Draw footer
        footer_y = height - 50
        if spec.source:
            draw.text((40, footer_y), f"Source: {spec.source}",
                     fill=colors['text_secondary'], font=font_small)
        if spec.time_period:
            draw.text((width//2, footer_y), spec.time_period,
                     fill=colors['text_secondary'], font=font_small, anchor="mt")
        if spec.show_branding:
            draw.text((width - 40, footer_y), "DataNarrative",
                     fill=colors['text_secondary'], font=font_small, anchor="rt")
        
        # Convert to bytes
        buf = io.BytesIO()
        img.save(buf, format='PNG', quality=95)
        buf.seek(0)
        
        render_time = (time.time() - start_time) * 1000
        
        return RenderOutput(
            success=True,
            image_bytes=buf.read(),
            format="png",
            width=width,
            height=height,
            render_time_ms=render_time,
            template_used="story_five_frame"
        )
    
    def _render_carousel(self, spec: RenderSpec, start_time: float) -> RenderOutput:
        """Render as carousel of 5 separate images"""
        import time
        
        colors = self.get_colors(spec.domain, spec.sentiment)
        
        width = self.STORY_WIDTH
        height = self.STORY_HEIGHT
        
        frames = spec.narrative_frames or []
        images = []
        
        # Load fonts
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            font_headline = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            font_metric = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_title = font_headline = font_body = font_metric = font_small = ImageFont.load_default()
        
        fonts = {
            'title': font_title,
            'headline': font_headline,
            'body': font_body,
            'metric': font_metric,
            'small': font_small
        }
        
        for i, frame in enumerate(frames[:5]):
            frame_img = self._render_single_frame(
                frame, i, len(frames),
                width, height,
                colors, fonts,
                spec
            )
            
            buf = io.BytesIO()
            frame_img.save(buf, format='PNG', quality=95)
            buf.seek(0)
            images.append(buf.read())
        
        render_time = (time.time() - start_time) * 1000
        
        return RenderOutput(
            success=True,
            image_bytes=images[0] if images else None,
            images=images,
            format="png",
            width=width,
            height=height,
            render_time_ms=render_time,
            template_used="story_carousel"
        )
    
    def _render_single_frame(
        self,
        frame: Dict,
        index: int,
        total: int,
        width: int,
        height: int,
        colors: Dict,
        fonts: Dict,
        spec: RenderSpec
    ) -> 'Image':
        """Render a single story frame as full image"""
        
        frame_type = frame.get('type', 'context')
        accent_color = self.FRAME_ACCENTS.get(frame_type, colors['primary'])
        
        img = Image.new('RGB', (width, height), colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Draw accent bar at top
        draw.rectangle([(0, 0), (width, 8)], fill=accent_color)
        
        # Draw frame number
        draw.text((width - 60, 30), f"{index + 1}/{total}",
                 fill=colors['text_secondary'], font=fonts['small'], anchor="rt")
        
        # Draw frame type label
        frame_label = frame_type.upper()
        draw.text((60, 50), frame_label, fill=accent_color, font=fonts['small'])
        
        # Draw headline
        headline = frame.get('headline', '')
        draw.text((width//2, height * 0.15), headline, fill=colors['text'],
                 font=fonts['headline'], anchor="mt")
        
        # Draw key metric if present
        key_metric = frame.get('key_metric')
        if key_metric:
            draw.text((width//2, height * 0.4), str(key_metric),
                     fill=accent_color, font=fonts['metric'], anchor="mm")
            
            metric_label = frame.get('key_metric_label', '')
            if metric_label:
                draw.text((width//2, height * 0.52), metric_label,
                         fill=colors['text_secondary'], font=fonts['body'], anchor="mt")
        
        # Draw body text
        body_text = frame.get('body_text', '')
        if body_text:
            # Word wrap
            max_width = width - 120
            lines = self._wrap_text(body_text, fonts['body'], max_width, draw)
            
            body_y = height * 0.65
            for line in lines[:5]:
                draw.text((width//2, body_y), line, fill=colors['text'],
                         font=fonts['body'], anchor="mt")
                body_y += 35
        
        # Draw series title at bottom
        draw.text((width//2, height - 80), spec.title,
                 fill=colors['text_secondary'], font=fonts['small'], anchor="mt")
        
        # Draw branding
        if spec.show_branding:
            draw.text((width//2, height - 40), "DataNarrative",
                     fill=colors['text_secondary'], font=fonts['small'], anchor="mt")
        
        return img
    
    def _draw_frame(
        self,
        draw: 'ImageDraw',
        frame: Dict,
        x: int,
        y: int,
        width: int,
        height: int,
        accent_color: str,
        fonts: Dict,
        colors: Dict
    ):
        """Draw a single frame panel within the combined image"""
        
        # Draw accent bar on left
        draw.rectangle([(x, y + 5), (x + 4, y + height - 5)], fill=accent_color)
        
        # Draw frame type label
        frame_type = frame.get('type', '').upper()
        draw.text((x + 15, y + 8), frame_type, fill=accent_color, font=fonts['small'])
        
        # Draw headline
        headline = frame.get('headline', '')
        draw.text((x + 15, y + 28), headline, fill=colors['text'], font=fonts['headline'])
        
        # Draw key metric if present
        key_metric = frame.get('key_metric')
        if key_metric:
            metric_x = x + width - 100
            draw.text((metric_x, y + 35), str(key_metric), fill=accent_color,
                     font=fonts['metric'], anchor="mt")
        
        # Draw body text (truncated)
        body_text = frame.get('body_text', '')[:150]
        if body_text:
            draw.text((x + 15, y + 60), body_text, fill=colors['text_secondary'],
                     font=fonts['body'])
    
    def _wrap_text(self, text: str, font, max_width: int, draw: 'ImageDraw') -> List[str]:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(test_line) * 10  # Fallback estimate
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines


# Register story renderer
from .base import TemplateRegistry
TemplateRegistry.register("story_five_frame", StoryRenderer)
TemplateRegistry.register("story_carousel", StoryRenderer)
