"""Embedding services."""

import hashlib
from typing import Any


class BgeM3EmbeddingService:
    """Embedding service backed by BGE-M3 with fallback."""

    def __init__(self, model_name: str, fallback_dim: int = 64) -> None:
        self.model_name = model_name
        self.fallback_dim = fallback_dim
        self._model: Any = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _fallback_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector: list[float] = []
        for i in range(self.fallback_dim):
            value = digest[i % len(digest)] / 255.0
            vector.append((value * 2.0) - 1.0)
        return vector

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for chunked texts."""
        if not texts:
            return []
        try:
            model = self._load_model()
            vectors = model.encode(texts, normalize_embeddings=True)
            return [list(map(float, row)) for row in vectors]
        except Exception:
            # Keep pipeline available even when model is not installed/loaded.
            return [self._fallback_embedding(t) for t in texts]

