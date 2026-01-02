"""
Knowledge Store
===============
Vector database for storing and retrieving knowledge chunks.
Uses ChromaDB for local, persistent storage.
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from ..models import DataChunk, Domain
from .embedder import Embedder, get_embedder

logger = logging.getLogger(__name__)

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    logger.warning("ChromaDB not installed - knowledge store will not persist")


class KnowledgeStore:
    """
    Vector-based knowledge store using ChromaDB.
    
    Features:
    - Persistent local storage
    - Semantic similarity search
    - Metadata filtering
    - Domain-aware retrieval
    
    Usage:
        store = KnowledgeStore("./storage/chroma")
        await store.add_chunks(chunks)
        results = await store.search("literacy trends in Telangana")
    """
    
    COLLECTION_NAME = "datanarrative_knowledge"
    
    def __init__(
        self, 
        persist_directory: str = "./storage/chroma",
        embedder: Optional[Embedder] = None
    ):
        """
        Initialize knowledge store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            embedder: Embedder instance (uses default if not provided)
        """
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.embedder = embedder or get_embedder()
        self.client = None
        self.collection = None
        
        self._init_store()
    
    def _init_store(self):
        """Initialize ChromaDB client and collection"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available - using in-memory fallback")
            self._chunks_memory = {}  # Fallback in-memory storage
            return
        
        try:
            # Initialize persistent client
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "DataNarrative knowledge base"}
            )
            
            logger.info(f"Knowledge store initialized at {self.persist_dir}")
            logger.info(f"Collection '{self.COLLECTION_NAME}' has {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None
            self._chunks_memory = {}
    
    async def add_chunks(self, chunks: List[DataChunk]) -> int:
        """
        Add chunks to the knowledge store.
        
        Args:
            chunks: List of DataChunk objects
            
        Returns:
            Number of chunks successfully added
        """
        if not chunks:
            return 0
        
        logger.info(f"Adding {len(chunks)} chunks to knowledge store")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        # Generate embeddings for all chunks
        texts_to_embed = [chunk.to_embedding_text() for chunk in chunks]
        all_embeddings = self.embedder.embed_batch(texts_to_embed)
        
        for chunk, embedding in zip(chunks, all_embeddings):
            ids.append(chunk.id)
            documents.append(chunk.content[:10000])  # Limit content size
            metadatas.append(self._chunk_to_metadata(chunk))
            embeddings.append(embedding)
        
        if self.collection:
            try:
                # Add to ChromaDB
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
                logger.info(f"Successfully added {len(chunks)} chunks")
                return len(chunks)
            except Exception as e:
                logger.error(f"Failed to add chunks: {e}")
                return 0
        else:
            # Fallback: in-memory storage
            for chunk, embedding in zip(chunks, embeddings):
                self._chunks_memory[chunk.id] = {
                    "chunk": chunk,
                    "embedding": embedding
                }
            return len(chunks)
    
    async def search(
        self,
        query: str,
        n_results: int = 10,
        domain_filter: Optional[str] = None,
        year_filter: Optional[int] = None,
        region_filter: Optional[str] = None,
        min_relevance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query
            n_results: Maximum number of results
            domain_filter: Filter by domain (e.g., "education")
            year_filter: Filter by year
            region_filter: Filter by region
            min_relevance: Minimum relevance score (0-1)
            
        Returns:
            List of results with content, metadata, and relevance scores
        """
        logger.info(f"Searching: '{query}' (n={n_results}, domain={domain_filter})")
        
        # Generate query embedding
        query_embedding = self.embedder.embed(query)
        
        # Build where filter
        where = self._build_where_filter(domain_filter, year_filter, region_filter)
        
        if self.collection:
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where if where else None,
                    include=["documents", "metadatas", "distances"]
                )
                
                return self._format_results(results, min_relevance)
                
            except Exception as e:
                logger.error(f"Search failed: {e}")
                return []
        else:
            # Fallback: simple in-memory search
            return self._memory_search(query_embedding, n_results, where)
    
    async def get_chunk(self, chunk_id: str) -> Optional[Dict]:
        """Get a specific chunk by ID"""
        if self.collection:
            try:
                results = self.collection.get(
                    ids=[chunk_id],
                    include=["documents", "metadatas"]
                )
                if results['ids']:
                    return {
                        "id": results['ids'][0],
                        "content": results['documents'][0],
                        "metadata": results['metadatas'][0]
                    }
            except Exception as e:
                logger.error(f"Failed to get chunk {chunk_id}: {e}")
        elif chunk_id in self._chunks_memory:
            chunk_data = self._chunks_memory[chunk_id]
            return {
                "id": chunk_id,
                "content": chunk_data["chunk"].content,
                "metadata": self._chunk_to_metadata(chunk_data["chunk"])
            }
        return None
    
    async def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk by ID"""
        if self.collection:
            try:
                self.collection.delete(ids=[chunk_id])
                return True
            except Exception as e:
                logger.error(f"Failed to delete chunk {chunk_id}: {e}")
                return False
        elif chunk_id in self._chunks_memory:
            del self._chunks_memory[chunk_id]
            return True
        return False
    
    async def delete_by_source(self, source_file: str) -> int:
        """Delete all chunks from a specific source file"""
        if self.collection:
            try:
                # Get all chunks from this source
                results = self.collection.get(
                    where={"source_file": source_file},
                    include=["metadatas"]
                )
                if results['ids']:
                    self.collection.delete(ids=results['ids'])
                    return len(results['ids'])
            except Exception as e:
                logger.error(f"Failed to delete by source: {e}")
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge store statistics"""
        if self.collection:
            total = self.collection.count()
            
            # Get domain distribution (sample-based for large collections)
            try:
                sample = self.collection.get(limit=1000, include=["metadatas"])
                domains = {}
                regions = set()
                sources = set()
                
                for meta in sample.get('metadatas', []):
                    domain = meta.get('domain', 'other')
                    domains[domain] = domains.get(domain, 0) + 1
                    if meta.get('region'):
                        regions.add(meta['region'])
                    if meta.get('source_file'):
                        sources.add(meta['source_file'])
                
                return {
                    "total_chunks": total,
                    "domains": domains,
                    "regions": list(regions),
                    "sources_count": len(sources),
                    "storage_path": str(self.persist_dir)
                }
            except:
                return {"total_chunks": total}
        else:
            return {
                "total_chunks": len(self._chunks_memory),
                "storage": "in-memory (fallback)"
            }
    
    def _chunk_to_metadata(self, chunk: DataChunk) -> Dict[str, Any]:
        """Convert DataChunk to ChromaDB metadata"""
        return {
            "source_file": chunk.source_file or "",
            "source_name": chunk.source_name or "",
            "domain": chunk.domain.value if chunk.domain else "other",
            "content_type": chunk.content_type or "text",
            "year": str(chunk.year) if chunk.year else "",
            "region": chunk.region or "",
            "has_historical_depth": str(chunk.has_historical_depth),
            "entities": ",".join(chunk.entities[:10]) if chunk.entities else "",
            "created_at": chunk.created_at.isoformat() if chunk.created_at else ""
        }
    
    def _build_where_filter(
        self,
        domain: Optional[str],
        year: Optional[int],
        region: Optional[str]
    ) -> Optional[Dict]:
        """Build ChromaDB where filter"""
        conditions = []
        
        if domain:
            conditions.append({"domain": domain})
        if year:
            conditions.append({"year": str(year)})
        if region:
            conditions.append({"region": region})
        
        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}
    
    def _format_results(
        self, 
        results: Dict, 
        min_relevance: float
    ) -> List[Dict[str, Any]]:
        """Format ChromaDB results"""
        formatted = []
        
        if not results.get('ids') or not results['ids'][0]:
            return []
        
        for i in range(len(results['ids'][0])):
            # Convert distance to relevance (ChromaDB uses L2 distance)
            distance = results['distances'][0][i]
            relevance = 1.0 / (1.0 + distance)  # Convert to 0-1 score
            
            if relevance < min_relevance:
                continue
            
            formatted.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "relevance": round(relevance, 4)
            })
        
        return formatted
    
    def _memory_search(
        self,
        query_embedding: List[float],
        n_results: int,
        where: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Fallback in-memory search"""
        import numpy as np
        
        results = []
        query_vec = np.array(query_embedding)
        
        for chunk_id, data in self._chunks_memory.items():
            chunk = data["chunk"]
            embedding = np.array(data["embedding"])
            
            # Check filters
            if where:
                meta = self._chunk_to_metadata(chunk)
                if not self._matches_filter(meta, where):
                    continue
            
            # Calculate cosine similarity
            similarity = np.dot(query_vec, embedding) / (
                np.linalg.norm(query_vec) * np.linalg.norm(embedding)
            )
            
            results.append({
                "id": chunk_id,
                "content": chunk.content,
                "metadata": self._chunk_to_metadata(chunk),
                "relevance": float(similarity)
            })
        
        # Sort by relevance and limit
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:n_results]
    
    def _matches_filter(self, metadata: Dict, where: Dict) -> bool:
        """Check if metadata matches filter"""
        if "$and" in where:
            return all(self._matches_filter(metadata, cond) for cond in where["$and"])
        
        for key, value in where.items():
            if metadata.get(key) != value:
                return False
        return True


# === Convenience functions ===

_store: Optional[KnowledgeStore] = None


def get_knowledge_store(persist_dir: str = "./storage/chroma") -> KnowledgeStore:
    """Get or create the global knowledge store"""
    global _store
    if _store is None:
        _store = KnowledgeStore(persist_dir)
    return _store
