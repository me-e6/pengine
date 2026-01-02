"""
Test Ingest Pipeline
====================
Quick test to verify the ingestion pipeline works.

Run with: python -m tests.test_ingest
"""

import sys
import asyncio
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ingest import (
    DataParser,
    SmartChunker,
    DomainTagger,
    IngestPipeline,
    parse_file,
    chunk_parsed_data
)


def test_parser():
    """Test the data parser"""
    print("\n" + "="*50)
    print("TEST: Data Parser")
    print("="*50)
    
    test_file = "storage/uploads/telangana_education_2015_2023.csv"
    
    result = parse_file(test_file)
    
    print(f"Success: {result.success}")
    print(f"Filename: {result.filename}")
    print(f"Tables found: {len(result.tables)}")
    print(f"Total rows: {result.total_rows}")
    
    if result.tables:
        table = result.tables[0]
        print(f"\nFirst table: {table.name}")
        print(f"  Columns: {table.columns}")
        print(f"  Rows: {table.row_count}")
        print(f"  Numeric columns: {table.numeric_columns}")
        print(f"  Has time dimension: {table.has_time_dimension}")
        print(f"  Time column: {table.time_column}")
        print(f"\nSample values:")
        for col, vals in list(table.sample_values.items())[:3]:
            print(f"  {col}: {vals}")
    
    return result


def test_chunker(parse_result):
    """Test the smart chunker"""
    print("\n" + "="*50)
    print("TEST: Smart Chunker")
    print("="*50)
    
    chunks = chunk_parsed_data(parse_result, "Telangana Education Statistics")
    
    print(f"Chunks created: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {chunk.content_type}")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Rows: {chunk.row_count}")
        print(f"  Has time: {chunk.has_time_dimension}")
        print(f"  Time range: {chunk.time_range}")
        print(f"  Key entities: {chunk.key_entities[:5]}")
        print(f"  Content preview: {chunk.content[:200]}...")
    
    return chunks


def test_tagger(chunks):
    """Test the domain tagger (rule-based, without API)"""
    print("\n" + "="*50)
    print("TEST: Domain Tagger (Rule-based)")
    print("="*50)
    
    tagger = DomainTagger(api_key=None)  # Use rule-based
    
    for chunk in chunks[:2]:  # Test first 2 chunks
        result = tagger._rule_based_tag(chunk)
        print(f"\nChunk: {chunk.chunk_id}")
        print(f"  Domain: {result.domain.value}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Year: {result.year}")
        print(f"  Region: {result.region}")
        print(f"  Quality: {result.data_quality}")


async def test_pipeline():
    """Test the complete pipeline"""
    print("\n" + "="*50)
    print("TEST: Complete Pipeline")
    print("="*50)
    
    pipeline = IngestPipeline(
        knowledge_store=None,  # No storage for test
        api_key=None  # Use rule-based tagging
    )
    
    result = await pipeline.ingest(
        "storage/uploads/telangana_education_2015_2023.csv",
        "Telangana Education Statistics 2015-2023",
        domain_hint="education"
    )
    
    print(f"\nPipeline Result:")
    print(f"  Success: {result.success}")
    print(f"  File ID: {result.file_id}")
    print(f"  Tables found: {result.tables_found}")
    print(f"  Chunks created: {result.chunks_created}")
    print(f"  Chunks tagged: {result.chunks_tagged}")
    print(f"  Domains detected: {result.domains_detected}")
    print(f"  Has historical data: {result.has_historical_data}")
    print(f"  Time range: {result.time_range}")
    print(f"  Regions detected: {result.regions_detected}")
    print(f"  Processing time: {result.processing_time_seconds:.2f}s")
    
    if result.errors:
        print(f"  Errors: {result.errors}")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# DATANARRATIVE - INGESTION PIPELINE TESTS")
    print("#"*60)
    
    # Test 1: Parser
    parse_result = test_parser()
    
    if not parse_result.success:
        print("\nParser failed! Cannot continue.")
        return
    
    # Test 2: Chunker
    chunks = test_chunker(parse_result)
    
    if not chunks:
        print("\nChunker produced no chunks! Cannot continue.")
        return
    
    # Test 3: Tagger (rule-based)
    test_tagger(chunks)
    
    # Test 4: Pipeline
    asyncio.run(test_pipeline())
    
    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETED")
    print("#"*60)


if __name__ == "__main__":
    main()
