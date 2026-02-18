"""RAG building blocks tests."""

from app.rag import BgeM3EmbeddingService, ChromaVectorStore, TextChunker


def test_chunker_basic_overlap() -> None:
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    chunks = chunker.chunk("abcdefghijklmnopqrstuvwxyz")
    assert len(chunks) >= 3
    assert chunks[0] == "abcdefghij"
    assert chunks[1].startswith("ijkl")


def test_embedding_fallback_vector_shape() -> None:
    service = BgeM3EmbeddingService(model_name="non-existent-model", fallback_dim=16)
    vectors = service.embed(["hello", "world"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 16
    assert all(-1.0 <= item <= 1.0 for item in vectors[0])


def test_vector_store_shape_validation() -> None:
    store = ChromaVectorStore(host="localhost", port=8001, collection_prefix="test")
    ok, err = store.upsert_document_chunks(
        knowledge_base_id=1,
        document_id=1,
        chunks=["a", "b"],
        embeddings=[[0.1, 0.2]],
    )
    assert ok is False
    assert err is not None

