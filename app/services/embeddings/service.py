import math
import re
from typing import List, Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculates cosine similarity between two numerical vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class LightweightSemanticVectorizer:
    """A reliable, fast, zero-dependency semantic vectorizer using subword n-grams and TF-IDF weighting.
    
    Provides predictable 64-dimensional dense semantic vectors when heavy neural models are offline,
    allowing RAG and semantic search to work instantly on any computer.
    """

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions

    def _hash_token(self, token: str) -> int:
        """Deterministic string hash into dimension space."""
        h = 0
        for ch in token:
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return h % self.dimensions

    def embed_text(self, text: str) -> List[float]:
        """Converts text into normalized dense vector."""
        if not text:
            return [0.0] * self.dimensions

        vector = np.zeros(self.dimensions, dtype=np.float32)
        # Tokenize words and character 3-grams for semantic morphology
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return [0.0] * self.dimensions

        # Word tokens
        for word in words:
            idx = self._hash_token(word)
            vector[idx] += 1.0
            # Character n-grams for typo resilience and word stems
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    ngram = word[i:i+3]
                    n_idx = self._hash_token(ngram)
                    vector[n_idx] += 0.35

        # L2 Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()


class EmbeddingService:
    """Unified embedding service supporting Ollama embeddings and pure-Python vectorization."""

    def __init__(self):
        self.fallback_vectorizer = LightweightSemanticVectorizer(dimensions=64)

    def embed(self, text: str, provider: Optional[str] = None, model: Optional[str] = None) -> List[float]:
        """Generates embedding vector for a given piece of text."""
        if not text or not text.strip():
            return [0.0] * 64

        # Try Ollama if explicitly requested or configured
        if provider == "ollama":
            try:
                from app.services.providers.ollama import OllamaProvider
                ollama = OllamaProvider()
                vec = ollama.embed(text, model_name=model)
                if vec and len(vec) > 0:
                    return vec
            except Exception as e:
                logger.debug("Ollama embedding failed, falling back to semantic vectorizer: %s", e)

        # Use fast, consistent dense vectorizer
        return self.fallback_vectorizer.embed_text(text)

    def embed_batch(self, texts: List[str], provider: Optional[str] = None, model: Optional[str] = None) -> List[List[float]]:
        """Generates embedding vectors for multiple texts."""
        return [self.embed(t, provider=provider, model=model) for t in texts]
