"""
Insight Detector
================
Analyzes retrieved data to detect meaningful insights.
Answers the four fundamental questions:
1. What is the data really saying?
2. What changed meaningfully?
3. Why does it matter to humans?
4. How should this be shown visually?
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    """Types of insights that can be detected"""
    GROWTH = "growth"           # Significant increase
    DECLINE = "decline"         # Significant decrease
    COMPARISON = "comparison"   # A vs B
    RANKING = "ranking"         # Top/bottom items
    DISTRIBUTION = "distribution"  # Parts of whole
    CORRELATION = "correlation"  # X relates to Y
    ANOMALY = "anomaly"         # Unusual value
    THRESHOLD = "threshold"     # Crossed important boundary
    STABILITY = "stability"     # No significant change


class Sentiment(str, Enum):
    """Emotional context of the insight"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    WARNING = "warning"


@dataclass
class DetectedInsight:
    """A single detected insight"""
    insight_type: InsightType
    summary: str                    # One-line summary
    
    # The change
    metric_name: str
    current_value: Any
    previous_value: Optional[Any] = None
    change_absolute: Optional[float] = None
    change_percentage: Optional[float] = None
    
    # Context
    direction: str = "stable"       # "up", "down", "stable"
    magnitude: str = "moderate"     # "small", "moderate", "large", "dramatic"
    velocity: str = "gradual"       # "gradual", "steady", "rapid", "sudden"
    
    # Human impact
    human_impact: str = ""
    sentiment: Sentiment = Sentiment.NEUTRAL
    
    # Visualization
    recommended_template: str = "hero_stat"
    confidence: float = 0.8
    
    # Evidence
    data_points: List[Dict] = field(default_factory=list)
    time_range: Optional[Tuple] = None
    
    def to_dict(self) -> Dict:
        return {
            "insight_type": self.insight_type.value,
            "summary": self.summary,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_absolute": self.change_absolute,
            "change_percentage": self.change_percentage,
            "direction": self.direction,
            "magnitude": self.magnitude,
            "velocity": self.velocity,
            "human_impact": self.human_impact,
            "sentiment": self.sentiment.value,
            "recommended_template": self.recommended_template,
            "confidence": self.confidence,
            "time_range": self.time_range,
        }


class InsightDetector:
    """
    Detects meaningful insights from data.
    
    Works with both raw data and retrieved chunks.
    Uses statistical analysis and domain knowledge.
    """
    
    # Thresholds for magnitude classification
    CHANGE_THRESHOLDS = {
        "small": 5,      # < 5% change
        "moderate": 15,  # 5-15% change
        "large": 30,     # 15-30% change
        "dramatic": 100  # > 30% change (capped display at 100)
    }
    
    # Domain-specific sentiment mapping
    POSITIVE_METRICS = [
        'literacy', 'enrollment', 'growth', 'income', 'revenue',
        'vaccination', 'employment', 'forest_cover', 'life_expectancy'
    ]
    
    NEGATIVE_METRICS = [
        'dropout', 'mortality', 'crime', 'pollution', 'unemployment',
        'poverty', 'disease', 'deaths', 'decline'
    ]
    
    def __init__(self):
        pass
    
    def detect_from_data(
        self,
        data: List[Dict],
        metric_column: str,
        time_column: Optional[str] = None,
        group_column: Optional[str] = None
    ) -> List[DetectedInsight]:
        """
        Detect insights from structured data.
        
        Args:
            data: List of data rows
            metric_column: Column containing the metric to analyze
            time_column: Column containing time/period
            group_column: Column to group by (e.g., district)
            
        Returns:
            List of detected insights
        """
        insights = []
        
        if not data or metric_column not in data[0]:
            return insights
        
        # If we have time dimension, detect trends
        if time_column and time_column in data[0]:
            trend_insights = self._detect_trends(data, metric_column, time_column)
            insights.extend(trend_insights)
        
        # If we have groups, detect comparisons/rankings
        if group_column and group_column in data[0]:
            comparison_insights = self._detect_comparisons(data, metric_column, group_column, time_column)
            insights.extend(comparison_insights)
        
        # Detect distribution if no groups
        if not group_column:
            dist_insight = self._detect_distribution(data, metric_column)
            if dist_insight:
                insights.append(dist_insight)
        
        # Detect anomalies
        anomaly_insights = self._detect_anomalies(data, metric_column, group_column)
        insights.extend(anomaly_insights)
        
        return insights
    
    def _detect_trends(
        self,
        data: List[Dict],
        metric_col: str,
        time_col: str
    ) -> List[DetectedInsight]:
        """Detect trend-based insights (growth/decline)"""
        insights = []
        
        # Sort by time
        try:
            sorted_data = sorted(data, key=lambda x: x.get(time_col, 0))
        except:
            sorted_data = data
        
        if len(sorted_data) < 2:
            return insights
        
        # Get first and last values
        first_row = sorted_data[0]
        last_row = sorted_data[-1]
        
        try:
            first_val = float(first_row.get(metric_col, 0))
            last_val = float(last_row.get(metric_col, 0))
        except (ValueError, TypeError):
            return insights
        
        if first_val == 0:
            return insights
        
        # Calculate change
        change_abs = last_val - first_val
        change_pct = (change_abs / first_val) * 100
        
        # Determine direction and type
        if change_pct > 2:
            insight_type = InsightType.GROWTH
            direction = "up"
        elif change_pct < -2:
            insight_type = InsightType.DECLINE
            direction = "down"
        else:
            insight_type = InsightType.STABILITY
            direction = "stable"
        
        # Determine magnitude
        abs_pct = abs(change_pct)
        if abs_pct < self.CHANGE_THRESHOLDS["small"]:
            magnitude = "small"
        elif abs_pct < self.CHANGE_THRESHOLDS["moderate"]:
            magnitude = "moderate"
        elif abs_pct < self.CHANGE_THRESHOLDS["large"]:
            magnitude = "large"
        else:
            magnitude = "dramatic"
        
        # Determine velocity (compare to middle point if available)
        if len(sorted_data) >= 3:
            mid_idx = len(sorted_data) // 2
            mid_val = float(sorted_data[mid_idx].get(metric_col, first_val))
            first_half_change = abs(mid_val - first_val)
            second_half_change = abs(last_val - mid_val)
            
            if second_half_change > first_half_change * 1.5:
                velocity = "accelerating"
            elif first_half_change > second_half_change * 1.5:
                velocity = "decelerating"
            else:
                velocity = "steady"
        else:
            velocity = "gradual"
        
        # Determine sentiment
        sentiment = self._determine_sentiment(metric_col, direction)
        
        # Generate human impact
        human_impact = self._generate_human_impact(
            metric_col, direction, magnitude, change_pct
        )
        
        # Select template
        template = self._select_template(insight_type, magnitude, len(sorted_data))
        
        # Build summary
        time_range = (first_row.get(time_col), last_row.get(time_col))
        summary = self._build_trend_summary(
            metric_col, direction, change_pct, time_range
        )
        
        insight = DetectedInsight(
            insight_type=insight_type,
            summary=summary,
            metric_name=metric_col,
            current_value=last_val,
            previous_value=first_val,
            change_absolute=round(change_abs, 2),
            change_percentage=round(change_pct, 2),
            direction=direction,
            magnitude=magnitude,
            velocity=velocity,
            human_impact=human_impact,
            sentiment=sentiment,
            recommended_template=template,
            confidence=0.85,
            data_points=sorted_data,
            time_range=time_range
        )
        
        insights.append(insight)
        return insights
    
    def _detect_comparisons(
        self,
        data: List[Dict],
        metric_col: str,
        group_col: str,
        time_col: Optional[str] = None
    ) -> List[DetectedInsight]:
        """Detect comparison/ranking insights"""
        insights = []
        
        # Get latest values per group
        group_values = {}
        
        for row in data:
            group = row.get(group_col)
            if not group:
                continue
            
            try:
                value = float(row.get(metric_col, 0))
            except:
                continue
            
            # If time column exists, prefer latest
            if time_col:
                time_val = row.get(time_col, 0)
                if group not in group_values or time_val > group_values[group][1]:
                    group_values[group] = (value, time_val)
            else:
                group_values[group] = (value, 0)
        
        if len(group_values) < 2:
            return insights
        
        # Sort by value
        sorted_groups = sorted(
            [(g, v[0]) for g, v in group_values.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Top performer
        top_group, top_val = sorted_groups[0]
        bottom_group, bottom_val = sorted_groups[-1]
        
        # Ranking insight
        ranking_summary = f"{top_group} leads with {metric_col} at {top_val:.1f}, while {bottom_group} trails at {bottom_val:.1f}"
        
        insights.append(DetectedInsight(
            insight_type=InsightType.RANKING,
            summary=ranking_summary,
            metric_name=metric_col,
            current_value=top_val,
            previous_value=bottom_val,
            change_absolute=round(top_val - bottom_val, 2),
            change_percentage=round(((top_val - bottom_val) / bottom_val) * 100 if bottom_val else 0, 2),
            direction="comparison",
            magnitude="large" if (top_val - bottom_val) / max(bottom_val, 1) > 0.2 else "moderate",
            human_impact=f"Gap between best and worst performers is {top_val - bottom_val:.1f} points",
            sentiment=Sentiment.NEUTRAL,
            recommended_template="ranking_bar",
            confidence=0.9,
            data_points=[{"group": g, "value": v} for g, v in sorted_groups]
        ))
        
        return insights
    
    def _detect_distribution(
        self,
        data: List[Dict],
        metric_col: str
    ) -> Optional[DetectedInsight]:
        """Detect distribution patterns"""
        values = []
        for row in data:
            try:
                values.append(float(row.get(metric_col, 0)))
            except:
                continue
        
        if len(values) < 3:
            return None
        
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Check for skewness
        skew_indicator = (mean_val - median_val) / stdev if stdev > 0 else 0
        
        if abs(skew_indicator) > 0.5:
            distribution_type = "skewed"
        else:
            distribution_type = "balanced"
        
        summary = f"{metric_col} has a {distribution_type} distribution with average {mean_val:.1f} (median: {median_val:.1f})"
        
        return DetectedInsight(
            insight_type=InsightType.DISTRIBUTION,
            summary=summary,
            metric_name=metric_col,
            current_value=mean_val,
            previous_value=median_val,
            magnitude="moderate",
            human_impact=f"Most values cluster around {median_val:.1f}",
            sentiment=Sentiment.NEUTRAL,
            recommended_template="pie_breakdown",
            confidence=0.75,
            data_points=[{"mean": mean_val, "median": median_val, "stdev": stdev}]
        )
    
    def _detect_anomalies(
        self,
        data: List[Dict],
        metric_col: str,
        group_col: Optional[str] = None
    ) -> List[DetectedInsight]:
        """Detect anomalous values"""
        insights = []
        
        values = []
        for row in data:
            try:
                values.append(float(row.get(metric_col, 0)))
            except:
                continue
        
        if len(values) < 5:
            return insights
        
        mean_val = statistics.mean(values)
        stdev = statistics.stdev(values)
        
        if stdev == 0:
            return insights
        
        # Find outliers (> 2 standard deviations)
        for row in data:
            try:
                val = float(row.get(metric_col, 0))
            except:
                continue
            
            z_score = (val - mean_val) / stdev
            
            if abs(z_score) > 2:
                group_name = row.get(group_col, "This value") if group_col else "This value"
                direction = "high" if z_score > 0 else "low"
                
                summary = f"{group_name} shows unusually {direction} {metric_col} at {val:.1f} (average: {mean_val:.1f})"
                
                insights.append(DetectedInsight(
                    insight_type=InsightType.ANOMALY,
                    summary=summary,
                    metric_name=metric_col,
                    current_value=val,
                    previous_value=mean_val,
                    change_percentage=round((val - mean_val) / mean_val * 100, 2),
                    direction=direction,
                    magnitude="dramatic",
                    human_impact=f"This is {abs(z_score):.1f} standard deviations from normal",
                    sentiment=Sentiment.WARNING,
                    recommended_template="hero_stat",
                    confidence=0.7,
                    data_points=[row]
                ))
        
        return insights[:3]  # Limit anomalies
    
    def _determine_sentiment(self, metric: str, direction: str) -> Sentiment:
        """Determine sentiment based on metric and direction"""
        metric_lower = metric.lower()
        
        is_positive_metric = any(p in metric_lower for p in self.POSITIVE_METRICS)
        is_negative_metric = any(n in metric_lower for n in self.NEGATIVE_METRICS)
        
        if direction == "up":
            if is_positive_metric:
                return Sentiment.POSITIVE
            elif is_negative_metric:
                return Sentiment.NEGATIVE
        elif direction == "down":
            if is_positive_metric:
                return Sentiment.NEGATIVE
            elif is_negative_metric:
                return Sentiment.POSITIVE
        
        return Sentiment.NEUTRAL
    
    def _generate_human_impact(
        self,
        metric: str,
        direction: str,
        magnitude: str,
        change_pct: float
    ) -> str:
        """Generate human-readable impact statement"""
        metric_clean = metric.replace('_', ' ').title()
        
        magnitude_words = {
            "small": "slightly",
            "moderate": "noticeably",
            "large": "significantly",
            "dramatic": "dramatically"
        }
        
        direction_words = {
            "up": "improved" if any(p in metric.lower() for p in self.POSITIVE_METRICS) else "increased",
            "down": "declined" if any(p in metric.lower() for p in self.POSITIVE_METRICS) else "decreased",
            "stable": "remained stable"
        }
        
        return f"{metric_clean} has {magnitude_words.get(magnitude, '')} {direction_words.get(direction, 'changed')} by {abs(change_pct):.1f}%"
    
    def _select_template(
        self,
        insight_type: InsightType,
        magnitude: str,
        data_points: int
    ) -> str:
        """Select best template for the insight"""
        template_map = {
            InsightType.GROWTH: "trend_line" if data_points > 3 else "hero_stat",
            InsightType.DECLINE: "trend_line" if data_points > 3 else "hero_stat",
            InsightType.COMPARISON: "versus",
            InsightType.RANKING: "ranking_bar",
            InsightType.DISTRIBUTION: "pie_breakdown",
            InsightType.CORRELATION: "trend_line",
            InsightType.ANOMALY: "hero_stat",
            InsightType.THRESHOLD: "hero_stat",
            InsightType.STABILITY: "hero_stat",
        }
        
        return template_map.get(insight_type, "hero_stat")
    
    def _build_trend_summary(
        self,
        metric: str,
        direction: str,
        change_pct: float,
        time_range: Tuple
    ) -> str:
        """Build a trend summary statement"""
        metric_clean = metric.replace('_', ' ').title()
        
        if direction == "up":
            verb = "increased"
        elif direction == "down":
            verb = "decreased"
        else:
            verb = "remained stable"
        
        return f"{metric_clean} {verb} by {abs(change_pct):.1f}% from {time_range[0]} to {time_range[1]}"


def detect_insights(
    data: List[Dict],
    metric_column: str,
    time_column: Optional[str] = None,
    group_column: Optional[str] = None
) -> List[DetectedInsight]:
    """Quick function to detect insights"""
    detector = InsightDetector()
    return detector.detect_from_data(data, metric_column, time_column, group_column)
