"""
Test Renderer Module
====================
Test chart generation, templates, and story rendering.

Run with: python -m tests.test_renderer
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.renderer import (
    RenderSpec, RenderOutput,
    ChartGenerator, get_chart_generator,
    RenderEngine, get_render_engine,
    TemplateRegistry
)


def test_chart_generator():
    """Test chart generation"""
    print("\n" + "="*50)
    print("TEST: Chart Generator")
    print("="*50)
    
    chart_gen = get_chart_generator()
    
    # Test data
    bar_data = [
        {"label": "Hyderabad", "value": 89.5},
        {"label": "Warangal", "value": 86.5},
        {"label": "Karimnagar", "value": 80.8},
        {"label": "Nizamabad", "value": 77.1},
        {"label": "Adilabad", "value": 74.2},
    ]
    
    line_data = [
        {"period": 2015, "value": 83.2},
        {"period": 2018, "value": 85.1},
        {"period": 2021, "value": 87.8},
        {"period": 2023, "value": 89.5},
    ]
    
    pie_data = [
        {"label": "Urban", "value": 65},
        {"label": "Rural", "value": 35},
    ]
    
    colors = {
        "primary": "#3B82F6",
        "secondary": "#93C5FD",
        "accent": "#10B981"
    }
    
    # Test bar chart
    print("\n1. Generating bar chart...")
    bar_bytes = chart_gen.create_bar_chart(bar_data, colors=colors, title="Literacy by District")
    print(f"   Bar chart: {len(bar_bytes)} bytes" if bar_bytes else "   Bar chart: FAILED (matplotlib not installed)")
    
    # Test line chart
    print("\n2. Generating line chart...")
    line_bytes = chart_gen.create_line_chart(line_data, colors=colors, title="Literacy Trend")
    print(f"   Line chart: {len(line_bytes)} bytes" if line_bytes else "   Line chart: FAILED")
    
    # Test pie chart
    print("\n3. Generating pie chart...")
    pie_bytes = chart_gen.create_pie_chart(pie_data, colors=colors, title="Urban vs Rural")
    print(f"   Pie chart: {len(pie_bytes)} bytes" if pie_bytes else "   Pie chart: FAILED")
    
    # Test hero number
    print("\n4. Generating hero number...")
    hero_bytes = chart_gen.create_hero_number(89.5, "Literacy Rate", change=7.6, unit="%", colors=colors)
    print(f"   Hero number: {len(hero_bytes)} bytes" if hero_bytes else "   Hero number: FAILED")
    
    return bar_bytes is not None or line_bytes is not None


def test_templates():
    """Test template rendering"""
    print("\n" + "="*50)
    print("TEST: Template Renderers")
    print("="*50)
    
    templates = TemplateRegistry.list_templates()
    print(f"\nRegistered templates: {templates}")
    
    engine = get_render_engine()
    
    # Test Hero Stat
    print("\n1. Testing Hero Stat template...")
    spec = RenderSpec(
        template_type="hero_stat",
        title="Telangana Literacy Rate 2023",
        subtitle="State Education Department Report",
        metrics=[{
            "value": 89.5,
            "label": "Literacy Rate",
            "change": 7.6,
            "unit": "%"
        }],
        insights=[
            "Highest literacy rate in state history",
            "Urban areas lead with 92.8%",
            "Rural literacy improved by 8.3%"
        ],
        domain="education",
        sentiment="positive",
        source="Census 2023"
    )
    
    result = engine.render(spec)
    print(f"   Hero Stat: success={result.success}, size={len(result.image_bytes) if result.image_bytes else 0} bytes")
    if result.success:
        path = engine.save(result, "test_hero_stat.png")
        print(f"   Saved to: {path}")
    
    # Test Trend Line
    print("\n2. Testing Trend Line template...")
    spec = RenderSpec(
        template_type="trend_line",
        title="Literacy Growth Trend",
        subtitle="Hyderabad District 2015-2023",
        chart_data=[
            {"period": 2015, "value": 83.2},
            {"period": 2018, "value": 85.1},
            {"period": 2021, "value": 87.8},
            {"period": 2023, "value": 89.5},
        ],
        metrics=[
            {"value": 89.5, "label": "Current"},
            {"value": 83.2, "label": "Baseline"},
            {"value": 7.6, "label": "Growth %"},
        ],
        insights=["Consistent growth over 8 years"],
        domain="education",
        sentiment="positive",
        source="Education Department"
    )
    
    result = engine.render(spec)
    print(f"   Trend Line: success={result.success}, size={len(result.image_bytes) if result.image_bytes else 0} bytes")
    if result.success:
        path = engine.save(result, "test_trend_line.png")
        print(f"   Saved to: {path}")
    
    # Test Ranking Bar
    print("\n3. Testing Ranking Bar template...")
    spec = RenderSpec(
        template_type="ranking_bar",
        title="District Literacy Rankings 2023",
        subtitle="Top 5 Districts by Literacy Rate",
        chart_data=[
            {"label": "Hyderabad", "value": 89.5},
            {"label": "Warangal", "value": 86.5},
            {"label": "Medchal", "value": 82.6},
            {"label": "Karimnagar", "value": 80.8},
            {"label": "Nizamabad", "value": 77.1},
        ],
        insights=["Hyderabad leads with 89.5% literacy rate"],
        domain="education",
        source="Census 2023"
    )
    
    result = engine.render(spec)
    print(f"   Ranking Bar: success={result.success}, size={len(result.image_bytes) if result.image_bytes else 0} bytes")
    if result.success:
        path = engine.save(result, "test_ranking_bar.png")
        print(f"   Saved to: {path}")
    
    # Test Versus
    print("\n4. Testing Versus template...")
    spec = RenderSpec(
        template_type="versus",
        title="Urban vs Rural Literacy",
        metrics=[
            {"value": 92.8, "label": "Urban"},
            {"value": 79.5, "label": "Rural"},
        ],
        insights=["Urban-rural gap narrowing but still significant"],
        domain="education",
        source="Census 2023"
    )
    
    result = engine.render(spec)
    print(f"   Versus: success={result.success}, size={len(result.image_bytes) if result.image_bytes else 0} bytes")
    if result.success:
        path = engine.save(result, "test_versus.png")
        print(f"   Saved to: {path}")
    
    return result.success


def test_story_mode():
    """Test story mode rendering"""
    print("\n" + "="*50)
    print("TEST: Story Mode Renderer")
    print("="*50)
    
    engine = get_render_engine()
    
    # Test 5-frame story
    print("\n1. Testing 5-Frame Story...")
    spec = RenderSpec(
        output_mode="story",
        template_type="story_five_frame",
        story_format="single",
        title="Telangana's Literacy Revolution",
        subtitle="A decade of educational transformation",
        narrative_frames=[
            {
                "type": "context",
                "headline": "Where We Started",
                "body_text": "In 2015, Telangana's literacy rate stood at 66.5%, below the national average.",
                "key_metric": "66.5%",
                "key_metric_label": "2015 Literacy Rate"
            },
            {
                "type": "change",
                "headline": "The Transformation",
                "body_text": "A decade of focused investment in education transformed the state's literacy landscape.",
                "key_metric": "+23%",
                "key_metric_label": "Growth"
            },
            {
                "type": "evidence",
                "headline": "The Numbers Speak",
                "body_text": "From 66.5% to 89.5% - consistent year-over-year improvement across all districts.",
                "key_metric": "89.5%",
                "key_metric_label": "2023 Literacy Rate"
            },
            {
                "type": "consequence",
                "headline": "Real Impact",
                "body_text": "Millions more citizens can now read, write, and participate fully in society.",
                "key_metric": "3.2M",
                "key_metric_label": "Newly Literate"
            },
            {
                "type": "implication",
                "headline": "What's Next",
                "body_text": "With strong foundations, Telangana aims for 95% literacy by 2030.",
                "key_metric": "95%",
                "key_metric_label": "2030 Target"
            }
        ],
        domain="education",
        sentiment="positive",
        source="Telangana Education Department",
        time_period="2015-2023"
    )
    
    result = engine.render(spec)
    print(f"   5-Frame Story: success={result.success}, size={len(result.image_bytes) if result.image_bytes else 0} bytes")
    if result.success:
        path = engine.save(result, "test_story.png")
        print(f"   Saved to: {path}")
    
    # Test carousel
    print("\n2. Testing Story Carousel...")
    spec.story_format = "carousel"
    
    result = engine.render(spec)
    print(f"   Carousel: success={result.success}, images={len(result.images)}")
    if result.success and result.images:
        paths = engine.save_carousel(result, prefix="test_carousel")
        print(f"   Saved {len(paths)} images")
    
    return result.success


def test_quick_render():
    """Test quick render helper"""
    print("\n" + "="*50)
    print("TEST: Quick Render")
    print("="*50)
    
    engine = get_render_engine()
    
    result = engine.render_quick(
        title="Telangana GDP Growth",
        value=12.5,
        label="Annual Growth Rate",
        change=2.3,
        domain="economy",
        template="hero_stat"
    )
    
    print(f"Quick render: success={result.success}")
    if result.success:
        path = engine.save(result, "test_quick.png")
        print(f"Saved to: {path}")
    
    return result.success


def test_template_list():
    """Test template listing"""
    print("\n" + "="*50)
    print("TEST: Template List")
    print("="*50)
    
    engine = get_render_engine()
    templates = engine.list_templates()
    
    print(f"\nAvailable templates ({len(templates)}):")
    for t in templates:
        print(f"\n  {t['id']}: {t.get('name', t['id'])}")
        print(f"    {t.get('description', 'No description')}")
        if t.get('best_for'):
            print(f"    Best for: {', '.join(t['best_for'])}")


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# DATANARRATIVE - RENDERER MODULE TESTS")
    print("#"*60)
    
    # Check dependencies
    try:
        import matplotlib
        print("\n✓ Matplotlib installed")
    except ImportError:
        print("\n✗ Matplotlib NOT installed - charts will not render")
    
    try:
        from PIL import Image
        print("✓ Pillow installed")
    except ImportError:
        print("✗ Pillow NOT installed - templates will not render")
    
    test_chart_generator()
    test_templates()
    test_story_mode()
    test_quick_render()
    test_template_list()
    
    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETED")
    print("#"*60)
    
    # List generated files
    output_dir = Path("./storage/outputs")
    if output_dir.exists():
        files = list(output_dir.glob("test_*.png"))
        if files:
            print(f"\nGenerated {len(files)} test images in ./storage/outputs/")


if __name__ == "__main__":
    main()
