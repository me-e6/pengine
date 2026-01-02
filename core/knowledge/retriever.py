"""
Retriever
=========
RAG-focused retrieval system that enhances search results
with context and relevance scoring.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .store import KnowledgeStore, get_knowledge_store
from ..models import Domain

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Enhanced retrieval result with context"""
    chunk_id: str
    content: str
    relevance: float
    
    # Metadata
    domain: str
    source: str
    year: Optional[str]
    region: Optional[str]
    has_historical_depth: bool
    
    # Context
    related_chunks: List[str]  # IDs of related chunks
    
    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "relevance": self.relevance,
            "domain": self.domain,
            "source": self.source,
            "year": self.year,
            "region": self.region,
            "has_historical_depth": self.has_historical_depth,
            "related_chunks": self.related_chunks
        }


@dataclass
class RetrievalContext:
    """Context from retrieval for the intelligence layer"""
    query: str
    results: List[RetrievalResult]
    
    # Aggregated info
    domains_found: List[str]
    has_historical_data: bool
    time_range: Optional[tuple]
    regions_covered: List[str]
    sources_used: List[str]
    
    # Quality
    total_results: int
    avg_relevance: float
    sufficient_context: bool  # Enough data to answer?


class Retriever:
    """
    RAG retriever that finds relevant context for queries.
    
    Features:
    - Multi-query retrieval
    - Context aggregation
    - Historical data detection
    - Domain-aware filtering
    
    Usage:
        retriever = Retriever(knowledge_store)
        context = await retriever.retrieve("literacy trends in Telangana")
    """
    
    def __init__(
        self,
        store: Optional[KnowledgeStore] = None,
        default_results: int = 10,
        min_relevance: float = 0.3
    ):
        """
        Initialize retriever.
        
        Args:
            store: KnowledgeStore instance
            default_results: Default number of results to retrieve
            min_relevance: Minimum relevance threshold
        """
        self.store = store or get_knowledge_store()
        self.default_results = default_results
        self.min_relevance = min_relevance
    
    async def retrieve(
        self,
        query: str,
        n_results: Optional[int] = None,
        domain_hint: Optional[str] = None,
        require_historical: bool = False
    ) -> RetrievalContext:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: Natural language query
            n_results: Number of results (default: 10)
            domain_hint: Hint about expected domain
            require_historical: Only return if historical data exists
            
        Returns:
            RetrievalContext with results and metadata
        """
        n_results = n_results or self.default_results
        
        logger.info(f"Retrieving context for: '{query}'")
        
        # Search knowledge store
        raw_results = await self.store.search(
            query=query,
            n_results=n_results,
            domain_filter=domain_hint,
            min_relevance=self.min_relevance
        )
        
        # Convert to RetrievalResults
        results = []
        for raw in raw_results:
            result = self._to_retrieval_result(raw)
            results.append(result)
        
        # If we need historical data but didn't find any, try broader search
        if require_historical and not any(r.has_historical_depth for r in results):
            logger.info("No historical data found, trying broader search")
            broader_results = await self.store.search(
                query=query,
                n_results=n_results * 2,
                min_relevance=self.min_relevance * 0.5
            )
            for raw in broader_results:
                result = self._to_retrieval_result(raw)
                if result.has_historical_depth and result not in results:
                    results.append(result)
        
        # Build context
        context = self._build_context(query, results)
        
        logger.info(
            f"Retrieved {len(results)} results, "
            f"historical={context.has_historical_data}, "
            f"domains={context.domains_found}"
        )
        
        return context
    
    async def retrieve_by_domain(
        self,
        domain: str,
        n_results: int = 20
    ) -> List[RetrievalResult]:
        """Retrieve chunks from a specific domain"""
        raw_results = await self.store.search(
            query=f"{domain} data statistics",
            n_results=n_results,
            domain_filter=domain
        )
        return [self._to_retrieval_result(r) for r in raw_results]
    
    async def retrieve_historical(
        self,
        topic: str,
        n_results: int = 20
    ) -> RetrievalContext:
        """
        Specifically retrieve historical/time-series data.
        Filters for chunks with time dimension.
        """
        # First search
        raw_results = await self.store.search(
            query=topic,
            n_results=n_results * 2  # Get more to filter
        )
        
        # Filter for historical data
        historical_results = []
        other_results = []
        
        for raw in raw_results:
            result = self._to_retrieval_result(raw)
            if result.has_historical_depth:
                historical_results.append(result)
            else:
                other_results.append(result)
        
        # Combine: historical first, then others
        results = historical_results + other_results[:n_results - len(historical_results)]
        results = results[:n_results]
        
        return self._build_context(topic, results)
    
    async def find_related(
        self,
        chunk_id: str,
        n_results: int = 5
    ) -> List[RetrievalResult]:
        """Find chunks related to a specific chunk"""
        # Get the original chunk
        chunk = await self.store.get_chunk(chunk_id)
        if not chunk:
            return []
        
        # Search using the chunk's content
        raw_results = await self.store.search(
            query=chunk['content'][:500],
            n_results=n_results + 1  # +1 to exclude self
        )
        
        # Filter out the original chunk
        results = []
        for raw in raw_results:
            if raw['id'] != chunk_id:
                results.append(self._to_retrieval_result(raw))
        
        return results[:n_results]
    
    def _to_retrieval_result(self, raw: Dict) -> RetrievalResult:
        """Convert raw search result to RetrievalResult"""
        metadata = raw.get('metadata', {})
        
        return RetrievalResult(
            chunk_id=raw['id'],
            content=raw['content'],
            relevance=raw.get('relevance', 0.0),
            domain=metadata.get('domain', 'other'),
            source=metadata.get('source_name', metadata.get('source_file', '')),
            year=metadata.get('year') or None,
            region=metadata.get('region') or None,
            has_historical_depth=metadata.get('has_historical_depth', 'False') == 'True',
            related_chunks=[]
        )
    
    def _build_context(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> RetrievalContext:
        """Build aggregated context from results"""
        
        # Aggregate domains
        domains = list(set(r.domain for r in results if r.domain))
        
        # Check for historical data
        has_historical = any(r.has_historical_depth for r in results)
        
        # Get time range
        years = []
        for r in results:
            if r.year:
                try:
                    years.append(int(r.year))
                except:
                    pass
        time_range = (min(years), max(years)) if len(years) >= 2 else None
        
        # Get regions
        regions = list(set(r.region for r in results if r.region))
        
        # Get sources
        sources = list(set(r.source for r in results if r.source))
        
        # Calculate average relevance
        avg_relevance = sum(r.relevance for r in results) / len(results) if results else 0
        
        # Determine if we have sufficient context
        sufficient = (
            len(results) >= 3 and
            avg_relevance >= self.min_relevance
        )
        
        return RetrievalContext(
            query=query,
            results=results,
            domains_found=domains,
            has_historical_data=has_historical,
            time_range=time_range,
            regions_covered=regions,
            sources_used=sources,
            total_results=len(results),
            avg_relevance=round(avg_relevance, 4),
            sufficient_context=sufficient
        )


# === Convenience function ===

async def retrieve_context(
    query: str,
    domain_hint: Optional[str] = None,
    require_historical: bool = False
) -> RetrievalContext:
    """Quick retrieval function"""
    retriever = Retriever()
    return await retriever.retrieve(
        query,
        domain_hint=domain_hint,
        require_historical=require_historical
    )
