"""Reranker service for retrieval results."""

from __future__ import annotations

from typing import Any


class BgeRerankerService:
    """Rerank retrieved chunks with a cross-encoder model."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3") -> None:
        self.model_name = model_name
        self._model: Any | None = None
        self._load_error: str | None = None

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        if self._load_error is not None:
            raise RuntimeError(self._load_error)
        try:
            from sentence_transformers import CrossEncoder  # type: ignore[import-untyped]

            self._model = CrossEncoder(self.model_name)
            return self._model
        except Exception as exc:  # noqa: BLE001
            self._load_error = f"加载 Reranker 模型失败: {exc}"
            raise RuntimeError(self._load_error) from exc

    @staticmethod
    def _fallback_score(query: str, content: str) -> float:
        """Very light lexical fallback score when model unavailable."""
        q_tokens = {t for t in query.strip().split() if t}
        c_tokens = {t for t in content.strip().split() if t}
        if not q_tokens or not c_tokens:
            return 0.0
        return len(q_tokens & c_tokens) / max(len(q_tokens), 1)

    def rerank(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        top_n: int,
    ) -> list[dict[str, Any]]:
        """Return top_n chunks sorted by rerank score descending."""
        if not chunks:
            return []
        if top_n <= 0:
            return []

        pairs = [(query, str(c.get("content", ""))) for c in chunks]
        try:
            model = self._get_model()
            scores = model.predict(pairs)
            scored = []
            for chunk, score in zip(chunks, scores):
                item = dict(chunk)
                item["rerank_score"] = float(score)
                scored.append(item)
            scored.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return scored[:top_n]
        except Exception:
            # Fallback to lexical overlap to avoid blocking QA flow.
            scored = []
            for chunk in chunks:
                item = dict(chunk)
                item["rerank_score"] = self._fallback_score(query, str(chunk.get("content", "")))
                scored.append(item)
            scored.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return scored[:top_n]

