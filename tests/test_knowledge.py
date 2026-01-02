"""
Test Knowledge Store
====================
Test the knowledge storage and retrieval system.

Run with: python -m tests.test_knowledge
"""

import sys
import asyncio
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ingest import parse_file, chunk_parsed_data, DomainTagger
from core.knowledge import KnowledgeStore, Retriever, embed_text
from core.models import DataChunk, Domain


async def test_embedder():
    """Test the embedder"""
    print("\n" + "="*50)
    print("TEST: Embedder")
    print("="*50)
    
    from core.knowledge import get_embedder
    
    embedder = get_embedder()
    
    text1 = "Literacy rate in Telangana increased from 65% to 72%"
    text2 = "Education statistics show improvement in school enrollment"
    text3 = "Agricultural production of cotton decreased significantly"
    
    emb1 = embedder.embed(text1)
    emb2 = embedder.embed(text2)
    emb3 = embedder.embed(text3)
    
    print(f"Embedding dimension: {len(emb1)}")
    print(f"Text 1: {text1[:50]}...")
    print(f"Text 2: {text2[:50]}...")
    print(f"Text 3: {text3[:50]}...")
    
    # Calculate similarity (dot product for normalized vectors)
    import numpy as np
    
    def cosine_sim(a, b):
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_12 = cosine_sim(emb1, emb2)
    sim_13 = cosine_sim(emb1, emb3)
    sim_23 = cosine_sim(emb2, emb3)
    
    print(f"\nSimilarity scores:")
    print(f"  Text1 vs Text2 (both education): {sim_12:.4f}")
    print(f"  Text1 vs Text3 (education vs agriculture): {sim_13:.4f}")
    print(f"  Text2 vs Text3 (education vs agriculture): {sim_23:.4f}")
    
    # Education texts should be more similar to each other than to agriculture
    if sim_12 > sim_13 and sim_12 > sim_23:
        print("  ✓ Embeddings correctly capture semantic similarity!")
    else:
        print("  ⚠ Using fallback embeddings (install sentence-transformers for better results)")


async def test_knowledge_store():
    """Test the knowledge store"""
    print("\n" + "="*50)
    print("TEST: Knowledge Store")
    print("="*50)
    
    # Create a temporary store
    store = KnowledgeStore(persist_directory="./storage/chroma_test")
    
    # Create test chunks
    chunks = [
        DataChunk(
            id="test_1",
            content="Literacy rate in Hyderabad increased from 83% in 2015 to 89% in 2023",
            domain=Domain.EDUCATION,
            year=2023,
            region="Telangana",
            has_historical_depth=True,
            entities=["Hyderabad", "literacy", "education"]
        ),
        DataChunk(
            id="test_2",
            content="Cotton production in Telangana declined by 15% due to irregular rainfall",
            domain=Domain.AGRICULTURE,
            year=2023,
            region="Telangana",
            has_historical_depth=False,
            entities=["cotton", "rainfall", "agriculture"]
        ),
        DataChunk(
            id="test_3",
            content="School enrollment in rural Telangana reached 95% in 2023",
            domain=Domain.EDUCATION,
            year=2023,
            region="Telangana",
            has_historical_depth=True,
            entities=["school", "enrollment", "rural"]
        ),
    ]
    
    # Add chunks
    added = await store.add_chunks(chunks)
    print(f"Added {added} chunks")
    
    # Get stats
    stats = store.get_stats()
    print(f"Store stats: {stats}")
    
    # Search
    print("\nSearch: 'education literacy'")
    results = await store.search("education literacy", n_results=5)
    for r in results:
        print(f"  [{r['relevance']:.3f}] {r['content'][:60]}...")
    
    # Search with domain filter
    print("\nSearch: 'Telangana' (domain=agriculture)")
    results = await store.search("Telangana", n_results=5, domain_filter="agriculture")
    for r in results:
        print(f"  [{r['relevance']:.3f}] {r['content'][:60]}...")
    
    return store


async def test_retriever(store):
    """Test the retriever"""
    print("\n" + "="*50)
    print("TEST: Retriever")
    print("="*50)
    
    retriever = Retriever(store=store)
    
    # Basic retrieval
    print("\nRetrieving context for: 'literacy trends in Telangana'")
    context = await retriever.retrieve("literacy trends in Telangana")
    
    print(f"Results found: {context.total_results}")
    print(f"Domains: {context.domains_found}")
    print(f"Has historical data: {context.has_historical_data}")
    print(f"Time range: {context.time_range}")
    print(f"Regions: {context.regions_covered}")
    print(f"Avg relevance: {context.avg_relevance}")
    print(f"Sufficient context: {context.sufficient_context}")
    
    print("\nTop results:")
    for r in context.results[:3]:
        print(f"  [{r.relevance:.3f}] [{r.domain}] {r.content[:60]}...")
    
    # Historical retrieval
    print("\n\nRetrieving historical data for: 'education statistics'")
    hist_context = await retriever.retrieve_historical("education statistics")
    
    print(f"Historical results: {len([r for r in hist_context.results if r.has_historical_depth])}")
    print(f"Total results: {hist_context.total_results}")


async def test_full_pipeline():
    """Test the complete ingest → store → retrieve pipeline"""
    print("\n" + "="*50)
    print("TEST: Full Pipeline (Ingest → Store → Retrieve)")
    print("="*50)
    
    # 1. Parse
    print("\n1. Parsing CSV...")
    parse_result = parse_file("storage/uploads/telangana_education_2015_2023.csv")
    print(f"   Parsed {parse_result.total_rows} rows")
    
    # 2. Chunk
    print("\n2. Chunking...")
    raw_chunks = chunk_parsed_data(parse_result, "Telangana Education Statistics")
    print(f"   Created {len(raw_chunks)} chunks")
    
    # 3. Tag
    print("\n3. Tagging...")
    tagger = DomainTagger(api_key=None)
    tagged_chunks = tagger.tag_chunks(raw_chunks)
    print(f"   Tagged {len(tagged_chunks)} chunks")
    
    # 4. Store
    print("\n4. Storing in knowledge base...")
    store = KnowledgeStore(persist_directory="./storage/chroma_full_test")
    added = await store.add_chunks(tagged_chunks)
    print(f"   Stored {added} chunks")
    
    # 5. Retrieve
    print("\n5. Testing retrieval...")
    retriever = Retriever(store=store)
    
    queries = [
        "How did literacy change in Hyderabad over the years?",
        "Which district has the lowest literacy rate?",
        "Compare urban and rural literacy in Telangana"
    ]
    
    for query in queries:
        print(f"\n   Query: '{query}'")
        context = await retriever.retrieve(query, n_results=3)
        print(f"   Found {context.total_results} results, historical={context.has_historical_data}")
        if context.results:
            print(f"   Top result [{context.results[0].relevance:.3f}]: {context.results[0].content[:80]}...")


async def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# DATANARRATIVE - KNOWLEDGE STORE TESTS")
    print("#"*60)
    
    await test_embedder()
    store = await test_knowledge_store()
    await test_retriever(store)
    await test_full_pipeline()
    
    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETED")
    print("#"*60)


if __name__ == "__main__":
    asyncio.run(main())
