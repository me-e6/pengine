"""
Test API Integration
====================
Test the complete API functionality.

Run with: python -m tests.test_api
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all modules import correctly"""
    print("\n" + "="*50)
    print("TEST: Module Imports")
    print("="*50)
    
    modules = [
        ("core.models", "DataChunk, Domain"),
        ("core.ingest", "IngestPipeline, DataParser"),
        ("core.knowledge", "KnowledgeStore, Retriever"),
        ("core.intelligence", "ReasoningEngine, QueryAnalyzer"),
        ("core.renderer", "RenderEngine, RenderSpec"),
        ("api.routes.query", "router"),
        ("api.routes.ingest", "router"),
        ("api.routes.render", "router"),
    ]
    
    success = 0
    failed = 0
    
    for module, items in modules:
        try:
            exec(f"from {module} import {items}")
            print(f"  ✓ {module}")
            success += 1
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            failed += 1
    
    print(f"\nResult: {success} passed, {failed} failed")
    return failed == 0


async def test_query_pipeline():
    """Test the full query → insight → render pipeline"""
    print("\n" + "="*50)
    print("TEST: Query Pipeline (End-to-End)")
    print("="*50)
    
    from core.intelligence import ReasoningEngine, QueryAnalyzer
    from core.renderer import RenderEngine, RenderSpec
    
    # Step 1: Analyze query
    print("\n1. Query Analysis")
    analyzer = QueryAnalyzer()
    analysis = analyzer.analyze("How has literacy changed in Telangana from 2015 to 2023?")
    
    print(f"   Intent: {analysis.intent.value}")
    print(f"   Domain: {analysis.domain_hint}")
    print(f"   Topics: {analysis.topics}")
    print(f"   Requires historical: {analysis.requires_historical}")
    print(f"   Preferred output: {analysis.preferred_output}")
    
    # Step 2: Run reasoning (without knowledge store for this test)
    print("\n2. Reasoning Engine")
    engine = ReasoningEngine(knowledge_store=None)
    result = await engine.reason("How has literacy changed in Telangana from 2015 to 2023?")
    
    print(f"   Output mode: {result.output_mode}")
    print(f"   Template: {result.recommended_template}")
    print(f"   Confidence: {result.overall_confidence}")
    print(f"   Notes: {result.reasoning_notes[:2]}")
    
    # Step 3: Render
    print("\n3. Render Output")
    render_engine = RenderEngine(output_dir="./storage/outputs")
    
    # Create a spec with sample data for testing
    spec = RenderSpec(
        output_mode="story",
        template_type="story_five_frame",
        title="Telangana Literacy Growth",
        subtitle="2015-2023 Education Report",
        narrative_frames=[
            {"type": "context", "headline": "Starting Point", "body_text": "In 2015, literacy was at 66.5%", "key_metric": "66.5%", "key_metric_label": "2015"},
            {"type": "change", "headline": "The Growth", "body_text": "Steady improvement year over year", "key_metric": "+23%", "key_metric_label": "Growth"},
            {"type": "evidence", "headline": "The Data", "body_text": "From 66.5% to 89.5%", "key_metric": "89.5%", "key_metric_label": "2023"},
            {"type": "consequence", "headline": "Impact", "body_text": "Millions more can now read and write", "key_metric": "3.2M", "key_metric_label": "Newly Literate"},
            {"type": "implication", "headline": "Future", "body_text": "On track for 95% by 2030", "key_metric": "95%", "key_metric_label": "Target"},
        ],
        domain="education",
        sentiment="positive",
        source="Census Data"
    )
    
    output = render_engine.render(spec)
    print(f"   Render success: {output.success}")
    print(f"   Size: {len(output.image_bytes) if output.image_bytes else 0} bytes")
    
    if output.success:
        path = render_engine.save(output, "test_api_pipeline.png")
        print(f"   Saved to: {path}")
    
    return output.success


async def test_ingest_pipeline():
    """Test the data ingestion pipeline"""
    print("\n" + "="*50)
    print("TEST: Ingest Pipeline")
    print("="*50)
    
    from core.ingest import IngestPipeline
    from core.knowledge import get_knowledge_store
    
    # Use the sample CSV
    csv_path = "./storage/uploads/telangana_education_2015_2023.csv"
    
    if not Path(csv_path).exists():
        print("   Sample CSV not found, skipping...")
        return True
    
    # Initialize pipeline
    knowledge_store = get_knowledge_store()
    pipeline = IngestPipeline(knowledge_store=knowledge_store)
    
    # Run ingestion
    print("\n1. Ingesting CSV...")
    result = await pipeline.ingest(csv_path, "Telangana Education Test")
    
    print(f"   Success: {result.success}")
    print(f"   Tables: {result.tables_found}")
    print(f"   Chunks created: {result.chunks_created}")
    print(f"   Chunks stored: {result.chunks_stored}")
    print(f"   Domains: {result.domains_detected}")
    print(f"   Has historical: {result.has_historical_data}")
    print(f"   Time range: {result.time_range}")
    
    if result.warnings:
        print(f"   Warnings: {result.warnings}")
    
    # Test retrieval
    print("\n2. Testing retrieval...")
    from core.knowledge import Retriever
    
    retriever = Retriever(store=knowledge_store)
    context = await retriever.retrieve("literacy rate Hyderabad")
    
    print(f"   Results found: {context.total_results}")
    print(f"   Has historical: {context.has_historical_data}")
    print(f"   Avg relevance: {context.avg_relevance:.3f}")
    
    if context.results:
        print(f"   Top result: {context.results[0].content[:100]}...")
    
    return result.success


def test_render_templates():
    """Test all render templates"""
    print("\n" + "="*50)
    print("TEST: All Render Templates")
    print("="*50)
    
    from core.renderer import RenderEngine, RenderSpec
    
    engine = RenderEngine(output_dir="./storage/outputs")
    templates = engine.list_templates()
    
    print(f"\nTesting {len(templates)} templates...")
    
    results = {}
    
    for template in templates:
        tid = template["id"]
        print(f"\n  {tid}:", end=" ")
        
        try:
            if tid in ["story_five_frame", "story_carousel"]:
                spec = RenderSpec(
                    output_mode="story",
                    template_type=tid,
                    story_format="single" if tid == "story_five_frame" else "carousel",
                    title="Test Story",
                    narrative_frames=[
                        {"type": "context", "headline": "Start", "body_text": "Test context", "key_metric": "100"},
                        {"type": "change", "headline": "Change", "body_text": "Test change", "key_metric": "+10%"},
                        {"type": "evidence", "headline": "Evidence", "body_text": "Test evidence", "key_metric": "110"},
                        {"type": "consequence", "headline": "Impact", "body_text": "Test impact"},
                        {"type": "implication", "headline": "Future", "body_text": "Test future"},
                    ],
                    domain="education"
                )
            elif tid == "versus":
                spec = RenderSpec(
                    template_type=tid,
                    title="Test Versus",
                    metrics=[
                        {"value": 80, "label": "Before"},
                        {"value": 90, "label": "After"}
                    ],
                    domain="education"
                )
            elif tid == "trend_line":
                spec = RenderSpec(
                    template_type=tid,
                    title="Test Trend",
                    chart_data=[
                        {"period": 2020, "value": 80},
                        {"period": 2021, "value": 85},
                        {"period": 2022, "value": 88},
                        {"period": 2023, "value": 90},
                    ],
                    metrics=[{"value": 90, "label": "Current"}],
                    domain="education"
                )
            elif tid == "ranking_bar":
                spec = RenderSpec(
                    template_type=tid,
                    title="Test Ranking",
                    chart_data=[
                        {"label": "Item A", "value": 90},
                        {"label": "Item B", "value": 85},
                        {"label": "Item C", "value": 80},
                    ],
                    domain="education"
                )
            else:  # hero_stat
                spec = RenderSpec(
                    template_type=tid,
                    title="Test Hero",
                    metrics=[{"value": 89.5, "label": "Test Metric", "change": 5.0}],
                    insights=["Test insight 1", "Test insight 2"],
                    domain="education"
                )
            
            output = engine.render(spec)
            
            if output.success:
                print(f"✓ ({len(output.image_bytes)} bytes)")
                results[tid] = True
            else:
                print(f"✗ ({output.error_message})")
                results[tid] = False
                
        except Exception as e:
            print(f"✗ (Exception: {e})")
            results[tid] = False
    
    passed = sum(1 for v in results.values() if v)
    print(f"\n  Result: {passed}/{len(templates)} templates working")
    
    return all(results.values())


async def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# DATANARRATIVE - API INTEGRATION TESTS")
    print("#"*60)
    
    all_passed = True
    
    # Test 1: Imports
    if not test_imports():
        all_passed = False
    
    # Test 2: Query Pipeline
    if not await test_query_pipeline():
        all_passed = False
    
    # Test 3: Ingest Pipeline
    if not await test_ingest_pipeline():
        all_passed = False
    
    # Test 4: Render Templates
    if not test_render_templates():
        all_passed = False
    
    print("\n" + "#"*60)
    if all_passed:
        print("# ALL TESTS PASSED ✓")
    else:
        print("# SOME TESTS FAILED ✗")
    print("#"*60)
    
    # List generated files
    output_dir = Path("./storage/outputs")
    if output_dir.exists():
        files = list(output_dir.glob("*.png"))
        print(f"\nGenerated {len(files)} images in ./storage/outputs/")


if __name__ == "__main__":
    asyncio.run(main())
