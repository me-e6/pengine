"""
Knowledge Module
================
Vector-based knowledge storage and retrieval for DataNarrative.

Components:
- Embedder: Generate text embeddings
- Store: ChromaDB-based vector store
- Retriever: RAG-focused retrieval
"""

from .embedder import (
    Embedder,
    get_embedder,
    embed_text,
    embed_texts,
)

from .store import (
    KnowledgeStore,
    get_knowledge_store,
)

from .retriever import (
    Retriever,
    RetrievalResult,
    RetrievalContext,
    retrieve_context,
)

__all__ = [
    # Embedder
    "Embedder",
    "get_embedder",
    "embed_text",
    "embed_texts",
    
    # Store
    "KnowledgeStore",
    "get_knowledge_store",
    
    # Retriever
    "Retriever",
    "RetrievalResult",
    "RetrievalContext",
    "retrieve_context",
]
