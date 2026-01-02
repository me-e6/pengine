"""
Test Intelligence Module
========================
Test the query analysis, insight detection, and narrative generation.

Run with: python -m tests.test_intelligence
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.intelligence import (
    QueryAnalyzer, QueryIntent, analyze_query,
    InsightDetector, InsightType, detect_insights,
    NarrativeGenerator, generate_narrative,
    ReasoningEngine
)


def test_query_analyzer():
    """Test query analysis"""
    print("\n" + "="*50)
    print("TEST: Query Analyzer")
    print("="*50)
    
    test_queries = [
        "How has literacy changed in Telangana from 2015 to 2023?",
        "Compare education in Hyderabad vs Warangal",
        "Which district has the highest literacy rate?",
        "What is the current enrollment rate?",
        "Show me the breakdown of urban vs rural literacy",
    ]
    
    analyzer = QueryAnalyzer()
    
    for query in test_queries:
        result = analyzer.analyze(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {result.intent.value} (confidence: {result.intent_confidence:.2f})")
        print(f"  Domain: {result.domain_hint}")
        print(f"  Topics: {result.topics}")
        print(f"  Locations: {result.locations}")
        print(f"  Time refs: {result.time_references}")
        print(f"  Needs historical: {result.requires_historical}")
        print(f"  Preferred output: {result.preferred_output}")


def test_insight_detector():
    """Test insight detection"""
    print("\n" + "="*50)
    print("TEST: Insight Detector")
    print("="*50)
    
    # Sample data
    test_data = [
        {"District": "Hyderabad", "Year": 2015, "Literacy_Rate": 83.2},
        {"District": "Hyderabad", "Year": 2018, "Literacy_Rate": 85.1},
        {"District": "Hyderabad", "Year": 2021, "Literacy_Rate": 87.8},
        {"District": "Hyderabad", "Year": 2023, "Literacy_Rate": 89.5},
        {"District": "Warangal", "Year": 2015, "Literacy_Rate": 78.4},
        {"District": "Warangal", "Year": 2018, "Literacy_Rate": 81.2},
        {"District": "Warangal", "Year": 2021, "Literacy_Rate": 84.1},
        {"District": "Warangal", "Year": 2023, "Literacy_Rate": 86.5},
        {"District": "Adilabad", "Year": 2015, "Literacy_Rate": 62.4},
        {"District": "Adilabad", "Year": 2018, "Literacy_Rate": 66.2},
        {"District": "Adilabad", "Year": 2021, "Literacy_Rate": 70.5},
        {"District": "Adilabad", "Year": 2023, "Literacy_Rate": 74.2},
    ]
    
    detector = InsightDetector()
    
    # Test trend detection
    print("\n1. Detecting trends in Literacy_Rate over Year:")
    hyderabad_data = [d for d in test_data if d["District"] == "Hyderabad"]
    insights = detector.detect_from_data(
        hyderabad_data,
        metric_column="Literacy_Rate",
        time_column="Year"
    )
    
    for insight in insights:
        print(f"\n  [{insight.insight_type.value}] {insight.summary}")
        print(f"    Direction: {insight.direction}, Magnitude: {insight.magnitude}")
        if insight.change_percentage is not None:
            print(f"    Change: {insight.change_percentage:.1f}%")
        print(f"    Sentiment: {insight.sentiment.value}")
        print(f"    Template: {insight.recommended_template}")
    
    # Test comparison/ranking
    print("\n2. Detecting rankings across districts (2023 data):")
    data_2023 = [d for d in test_data if d["Year"] == 2023]
    insights = detector.detect_from_data(
        data_2023,
        metric_column="Literacy_Rate",
        group_column="District"
    )
    
    for insight in insights:
        print(f"\n  [{insight.insight_type.value}] {insight.summary}")


def test_narrative_generator():
    """Test narrative generation"""
    print("\n" + "="*50)
    print("TEST: Narrative Generator")
    print("="*50)
    
    # Create a sample insight
    from core.intelligence.detector import DetectedInsight, InsightType, Sentiment
    
    insight = DetectedInsight(
        insight_type=InsightType.GROWTH,
        summary="Literacy Rate increased by 7.6% from 2015 to 2023",
        metric_name="Literacy_Rate",
        current_value=89.5,
        previous_value=83.2,
        change_absolute=6.3,
        change_percentage=7.6,
        direction="up",
        magnitude="moderate",
        velocity="steady",
        human_impact="Literacy has noticeably improved by 7.6%",
        sentiment=Sentiment.POSITIVE,
        recommended_template="trend_line",
        confidence=0.85,
        time_range=(2015, 2023)
    )
    
    generator = NarrativeGenerator()
    narrative = generator.generate(
        insight,
        domain="education",
        source="Telangana Education Statistics"
    )
    
    print(f"\nTitle: {narrative.title}")
    print(f"Subtitle: {narrative.subtitle}")
    print(f"Period: {narrative.time_period}")
    print(f"Sentiment: {narrative.sentiment}")
    
    print("\nStory Frames:")
    for frame in narrative.get_frames():
        print(f"\n  {frame.frame_type.upper()}")
        print(f"    Headline: {frame.headline}")
        print(f"    Body: {frame.body_text[:100]}...")
        if frame.key_metric:
            print(f"    Key Metric: {frame.key_metric} ({frame.key_metric_label})")


async def test_reasoning_engine():
    """Test the full reasoning pipeline"""
    print("\n" + "="*50)
    print("TEST: Reasoning Engine (without knowledge store)")
    print("="*50)
    
    engine = ReasoningEngine(knowledge_store=None)
    
    queries = [
        "How has literacy changed in Telangana?",
        "Which district has the best education?",
        "What is the current state of schools?",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        result = await engine.reason(query)
        
        print(f"  Intent: {result.query_analysis.intent.value}")
        print(f"  Context found: {result.context_found}")
        print(f"  Output mode: {result.output_mode}")
        print(f"  Template: {result.recommended_template}")
        print(f"  Confidence: {result.overall_confidence:.2f}")
        print(f"  Reasoning notes:")
        for note in result.reasoning_notes[:3]:
            print(f"    - {note}")


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# DATANARRATIVE - INTELLIGENCE MODULE TESTS")
    print("#"*60)
    
    test_query_analyzer()
    test_insight_detector()
    test_narrative_generator()
    asyncio.run(test_reasoning_engine())
    
    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETED")
    print("#"*60)


if __name__ == "__main__":
    main()
