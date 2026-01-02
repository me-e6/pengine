"""
Embedder
========
Generates embeddings for text chunks using sentence-transformers.
Free, local, no API required.
"""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    logger.warning("sentence-transformers not installed - using fallback embeddings")


class Embedder:
    """
    Generates embeddings for text using sentence-transformers.
    
    Default model: all-MiniLM-L6-v2
    - Fast and lightweight
    - 384 dimensions
    - Good quality for retrieval
    - Runs locally, no API needed
    """
    
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedder.
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("Using fallback hash-based embeddings")
            return
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            List of floats (embedding vector)
        """
        if self.model:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            return self._fallback_embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        More efficient than calling embed() repeatedly.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        if self.model:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
        else:
            return [self._fallback_embed(text) for text in texts]
    
    def _fallback_embed(self, text: str) -> List[float]:
        """
        Fallback embedding when sentence-transformers is not available.
        Uses deterministic hash-based pseudo-embeddings.
        
        NOTE: This is NOT suitable for production semantic search.
        Install sentence-transformers for proper embeddings.
        """
        import hashlib
        
        # Create multiple hashes for more dimensions
        embeddings = []
        for i in range(24):  # 24 * 16 = 384 dimensions
            salted = f"{text}_{i}"
            hash_bytes = hashlib.md5(salted.encode()).digest()
            # Convert bytes to floats between -1 and 1
            for byte in hash_bytes:
                normalized = (byte / 127.5) - 1.0
                embeddings.append(normalized)
        
        return embeddings[:self.EMBEDDING_DIM]
    
    def get_dimension(self) -> int:
        """Get the embedding dimension"""
        return self.EMBEDDING_DIM


# === Global instance for convenience ===
_embedder: Optional[Embedder] = None


def get_embedder() -> Embedder:
    """Get or create the global embedder instance"""
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


def embed_text(text: str) -> List[float]:
    """Quick function to embed a single text"""
    return get_embedder().embed(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Quick function to embed multiple texts"""
    return get_embedder().embed_batch(texts)
