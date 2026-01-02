"""
Chart Generators
================
Creates charts using Matplotlib.
Bar, Line, Pie, and Comparison charts.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
import io

logger = logging.getLogger(__name__)

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    logger.warning("Matplotlib not installed - charts will not render")


class ChartGenerator:
    """
    Generates charts for infographics.
    
    All methods return bytes (PNG image) or Figure object.
    """
    
    def __init__(self):
        if MATPLOTLIB_AVAILABLE:
            # Set default style
            plt.style.use('seaborn-v0_8-whitegrid')
    
    def create_bar_chart(
        self,
        data: List[Dict],
        x_key: str = "label",
        y_key: str = "value",
        colors: Optional[Dict] = None,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        horizontal: bool = False
    ) -> bytes:
        """
        Create a bar chart.
        
        Args:
            data: List of {"label": "X", "value": 100, ...}
            x_key: Key for x-axis labels
            y_key: Key for y-axis values
            colors: Color configuration
            title: Chart title
            figsize: Figure size in inches
            horizontal: If True, create horizontal bars
            
        Returns:
            PNG image bytes
        """
        if not MATPLOTLIB_AVAILABLE:
            return b""
        
        colors = colors or {}
        primary = colors.get("primary", "#3B82F6")
        
        fig, ax = plt.subplots(figsize=figsize)
        
        labels = [d.get(x_key, "") for d in data]
        values = [float(d.get(y_key, 0)) for d in data]
        
        # Create gradient colors based on values
        max_val = max(values) if values else 1
        bar_colors = [self._adjust_color_intensity(primary, v/max_val) for v in values]
        
        if horizontal:
            bars = ax.barh(labels, values, color=bar_colors, edgecolor='white', linewidth=0.5)
            ax.set_xlabel(y_key.replace('_', ' ').title())
        else:
            bars = ax.bar(labels, values, color=bar_colors, edgecolor='white', linewidth=0.5)
            ax.set_ylabel(y_key.replace('_', ' ').title())
            plt.xticks(rotation=45, ha='right')
        
        # Add value labels
        for bar, val in zip(bars, values):
            if horizontal:
                ax.text(bar.get_width() + max_val*0.01, bar.get_y() + bar.get_height()/2,
                       f'{val:.1f}', va='center', fontsize=10, fontweight='bold')
            else:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.01,
                       f'{val:.1f}', ha='center', fontsize=10, fontweight='bold')
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig)
    
    def create_line_chart(
        self,
        data: List[Dict],
        x_key: str = "period",
        y_key: str = "value",
        colors: Optional[Dict] = None,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        show_points: bool = True,
        fill_under: bool = True
    ) -> bytes:
        """
        Create a line/trend chart.
        
        Args:
            data: List of {"period": 2015, "value": 83.2, ...}
            x_key: Key for x-axis
            y_key: Key for y-axis values
            colors: Color configuration
            title: Chart title
            figsize: Figure size
            show_points: Show data point markers
            fill_under: Fill area under line
            
        Returns:
            PNG image bytes
        """
        if not MATPLOTLIB_AVAILABLE:
            return b""
        
        colors = colors or {}
        primary = colors.get("primary", "#3B82F6")
        secondary = colors.get("secondary", "#93C5FD")
        
        fig, ax = plt.subplots(figsize=figsize)
        
        x_vals = [d.get(x_key, i) for i, d in enumerate(data)]
        y_vals = [float(d.get(y_key, 0)) for d in data]
        
        # Plot line
        line, = ax.plot(x_vals, y_vals, color=primary, linewidth=3, marker='o' if show_points else None,
                       markersize=8, markerfacecolor='white', markeredgewidth=2)
        
        # Fill under curve
        if fill_under:
            ax.fill_between(x_vals, y_vals, alpha=0.2, color=primary)
        
        # Add value labels at points
        if show_points:
            for x, y in zip(x_vals, y_vals):
                ax.annotate(f'{y:.1f}', (x, y), textcoords="offset points",
                           xytext=(0, 10), ha='center', fontsize=9, fontweight='bold')
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        ax.set_xlabel(x_key.replace('_', ' ').title())
        ax.set_ylabel(y_key.replace('_', ' ').title())
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig)
    
    def create_pie_chart(
        self,
        data: List[Dict],
        label_key: str = "label",
        value_key: str = "value",
        colors: Optional[Dict] = None,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (8, 8)
    ) -> bytes:
        """
        Create a pie/donut chart.
        
        Args:
            data: List of {"label": "Urban", "value": 65, ...}
            label_key: Key for labels
            value_key: Key for values
            colors: Color configuration
            title: Chart title
            figsize: Figure size
            
        Returns:
            PNG image bytes
        """
        if not MATPLOTLIB_AVAILABLE:
            return b""
        
        fig, ax = plt.subplots(figsize=figsize)
        
        labels = [d.get(label_key, "") for d in data]
        values = [float(d.get(value_key, 0)) for d in data]
        
        # Generate colors
        primary = (colors or {}).get("primary", "#3B82F6")
        pie_colors = self._generate_color_palette(primary, len(values))
        
        # Create donut chart
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels,
            colors=pie_colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.75,
            wedgeprops=dict(width=0.5, edgecolor='white')
        )
        
        # Style text
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig)
    
    def create_comparison_chart(
        self,
        data: List[Dict],
        label_key: str = "label",
        value_a_key: str = "value_a",
        value_b_key: str = "value_b",
        legend_a: str = "Before",
        legend_b: str = "After",
        colors: Optional[Dict] = None,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6)
    ) -> bytes:
        """
        Create a grouped bar comparison chart.
        
        Args:
            data: List of {"label": "X", "value_a": 80, "value_b": 90, ...}
            label_key: Key for category labels
            value_a_key: Key for first value set
            value_b_key: Key for second value set
            legend_a: Label for first set
            legend_b: Label for second set
            colors: Color configuration
            title: Chart title
            figsize: Figure size
            
        Returns:
            PNG image bytes
        """
        if not MATPLOTLIB_AVAILABLE:
            return b""
        
        import numpy as np
        
        colors = colors or {}
        color_a = colors.get("secondary", "#93C5FD")
        color_b = colors.get("primary", "#3B82F6")
        
        fig, ax = plt.subplots(figsize=figsize)
        
        labels = [d.get(label_key, "") for d in data]
        values_a = [float(d.get(value_a_key, 0)) for d in data]
        values_b = [float(d.get(value_b_key, 0)) for d in data]
        
        x = np.arange(len(labels))
        width = 0.35
        
        bars_a = ax.bar(x - width/2, values_a, width, label=legend_a, color=color_a, edgecolor='white')
        bars_b = ax.bar(x + width/2, values_b, width, label=legend_b, color=color_b, edgecolor='white')
        
        # Add value labels
        for bars in [bars_a, bars_b]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_ylabel('Value')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig)
    
    def create_hero_number(
        self,
        value: Any,
        label: str,
        change: Optional[float] = None,
        unit: str = "",
        colors: Optional[Dict] = None,
        figsize: Tuple[int, int] = (6, 4)
    ) -> bytes:
        """
        Create a hero number display.
        
        Args:
            value: The main number to display
            label: Label for the number
            change: Percentage change (shows arrow)
            unit: Unit suffix (%, pts, etc.)
            colors: Color configuration
            figsize: Figure size
            
        Returns:
            PNG image bytes
        """
        if not MATPLOTLIB_AVAILABLE:
            return b""
        
        colors = colors or {}
        primary = colors.get("primary", "#3B82F6")
        positive = colors.get("accent", "#10B981")
        negative = "#EF4444"
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Format value
        if isinstance(value, float):
            value_str = f"{value:.1f}{unit}"
        else:
            value_str = f"{value}{unit}"
        
        # Main number
        ax.text(5, 6, value_str, fontsize=72, fontweight='bold', 
               ha='center', va='center', color=primary)
        
        # Label
        ax.text(5, 3, label, fontsize=18, ha='center', va='center', 
               color='#64748B')
        
        # Change indicator
        if change is not None:
            change_color = positive if change >= 0 else negative
            arrow = "▲" if change >= 0 else "▼"
            ax.text(5, 1.5, f"{arrow} {abs(change):.1f}%", fontsize=14, 
                   ha='center', va='center', color=change_color, fontweight='bold')
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig)
    
    def _fig_to_bytes(self, fig: 'Figure') -> bytes:
        """Convert matplotlib figure to PNG bytes"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    
    def _adjust_color_intensity(self, hex_color: str, intensity: float) -> str:
        """Adjust color intensity (0-1 scale)"""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Adjust towards white for lower intensity
        factor = 0.3 + (intensity * 0.7)  # Range 0.3-1.0
        r = int(r * factor + 255 * (1 - factor))
        g = int(g * factor + 255 * (1 - factor))
        b = int(b * factor + 255 * (1 - factor))
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _generate_color_palette(self, base_color: str, n: int) -> List[str]:
        """Generate n colors from a base color"""
        if n <= 0:
            return []
        
        colors = []
        for i in range(n):
            intensity = 0.4 + (0.6 * (n - i) / n)
            colors.append(self._adjust_color_intensity(base_color, intensity))
        
        return colors


# Global instance
_chart_generator: Optional[ChartGenerator] = None


def get_chart_generator() -> ChartGenerator:
    """Get or create chart generator instance"""
    global _chart_generator
    if _chart_generator is None:
        _chart_generator = ChartGenerator()
    return _chart_generator
