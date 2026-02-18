"""Keyword-based retrieval: re-score vector candidates by term overlap (complements vector search)."""

import re
from app.rag.embedding import BgeM3EmbeddingService
from app.rag.vector_store import ChromaVectorStore


def _tokenize_for_keyword(text: str) -> list[str]:
    """Simple tokenize: split by non-alnum and keep words >= 1 char."""
    tokens = re.findall(r"[a-zA-Z0-9]+|[^\s\w]", text)
    return [t for t in tokens if len(t) >= 1]


class KeywordRetriever:
    """Retrieve chunks by querying vector store with larger k then re-ranking by keyword overlap."""

    def __init__(
        self,
        embedding_service: BgeM3EmbeddingService,
        vector_store: ChromaVectorStore,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        knowledge_base_id: int,
        query: str,
        top_k: int = 5,
        candidate_multiplier: int = 4,
    ) -> tuple[list[dict], str | None]:
        """Get more candidates from vector store, then re-rank by keyword overlap."""
        cleaned = query.strip()
        if not cleaned:
            return [], "query 不能为空"
        query_embedding = self.embedding_service.embed([cleaned])[0]
        n_results = max(top_k * candidate_multiplier, 20)
        rows, err = self.vector_store.query_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_embedding,
            top_k=n_results,
        )
        if err is not None:
            return [], err
        terms = set(_tokenize_for_keyword(cleaned.lower()))
        if not terms:
            return rows[:top_k], None
        scored = []
        for r in rows:
            content = (r.get("content") or "").lower()
            score = sum(1 for t in terms if t in content)
            scored.append((score, r))
        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:top_k]], None
