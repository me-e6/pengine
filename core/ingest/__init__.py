"""
Ingest Module
=============
Data ingestion pipeline for DataNarrative.

Components:
- Parser: Read CSV/Excel files
- Chunker: Smart data segmentation
- Tagger: AI-powered domain detection
- Pipeline: Complete ingestion flow
"""

from .parser import (
    DataParser,
    ParseResult,
    ParsedTable,
    parse_file,
)

from .chunker import (
    SmartChunker,
    DataChunkRaw,
    chunk_parsed_data,
)

from .tagger import (
    DomainTagger,
    TaggingResult,
    tag_chunks_with_ai,
    detect_domain,
)

from .pipeline import (
    IngestPipeline,
    IngestResult,
    ingest_file,
)

__all__ = [
    # Parser
    "DataParser",
    "ParseResult", 
    "ParsedTable",
    "parse_file",
    
    # Chunker
    "SmartChunker",
    "DataChunkRaw",
    "chunk_parsed_data",
    
    # Tagger
    "DomainTagger",
    "TaggingResult",
    "tag_chunks_with_ai",
    "detect_domain",
    
    # Pipeline
    "IngestPipeline",
    "IngestResult",
    "ingest_file",
]
