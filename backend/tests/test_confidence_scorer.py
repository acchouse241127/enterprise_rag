"""Retriever tests."""

from app.rag.retriever import VectorRetriever


class _FakeEmbeddingService:
    def embed(self, texts: list[str]) -> list[list[float]]:
        assert texts == ["养老金投资策略"]
        return [[0.1, 0.2, 0.3]]


class _FakeVectorStore:
    def query_knowledge_base(
        self,
        knowledge_base_id: int,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> tuple[list[dict], str | None]:
        assert knowledge_base_id == 10
        assert query_embedding == [0.1, 0.2, 0.3]
        assert top_k == 3
        return [
            {"chunk_id": "doc1_chunk0", "content": "稳健配置", "metadata": {"document_id": 1}, "distance": 0.08}
        ], None


def test_retriever_basic() -> None:
    retriever = VectorRetriever(
        embedding_service=_FakeEmbeddingService(),
        vector_store=_FakeVectorStore(),
    )
    rows, err = retriever.retrieve(knowledge_base_id=10, query="养老金投资策略", top_k=3)
    assert err is None
    assert len(rows) == 1
    assert rows[0]["chunk_id"] == "doc1_chunk0"


def test_retriever_empty_query() -> None:
    retriever = VectorRetriever(
        embedding_service=_FakeEmbeddingService(),
        vector_store=_FakeVectorStore(),
    )
    rows, err = retriever.retrieve(knowledge_base_id=10, query="   ", top_k=3)
    assert rows == []
    assert err is not None
