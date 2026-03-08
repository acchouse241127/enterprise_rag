"""
Unit tests for ChromaVectorStore.

Tests for app/rag/vector_store.py
Author: C2
"""

import pytest
from unittest.mock import MagicMock, patch


class TestChromaVectorStoreInit:
    """Tests for ChromaVectorStore initialization."""

    def test_init_success(self):
        """Test successful initialization."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)
            assert store._client == mock_client

    def test_init_with_credentials(self):
        """Test initialization with credentials."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        with patch("chromadb.Client") as MockClient:
            MockClient.return_value = mock_client
            store = ChromaVectorStore(
                host="localhost",
                port=8000,
                chroma_user="admin",
                chroma_password="password"
            )
            MockClient.assert_called_once()


class TestChromaVectorStoreCollections:
    """Tests for collection management."""

    def test_list_collections_success(self):
        """Test list_collections returns collections."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_collections = [MagicMock(name="kb_1"), MagicMock(name="kb_2")]
        mock_client.list_collections.return_value = mock_collections

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)
            result = store.list_collections()
            assert result == mock_collections

    def test_get_or_create_collection_new(self):
        """Test get_or_create_collection creates new collection."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_client.get_collection.return_value = None

        mock_collection = MagicMock()
        mock_client.create_collection.return_value = mock_collection

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)
            result = store.get_or_create_collection("kb_1")
            assert result == mock_collection
            mock_client.create_collection.assert_called()

    def test_get_or_create_collection_existing(self):
        """Test get_or_create_collection returns existing collection."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)
            result = store.get_or_create_collection("kb_1")
            assert result == mock_collection
            mock_client.create_collection.assert_not_called()


class TestChromaVectorStoreUpsert:
    """Tests for upsert operations."""

    def test_upsert_document_chunks_success(self):
        """Test successful chunk upsert."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_collection = MagicMock()

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            chunks = ["chunk1", "chunk2"]
            embeddings = [[0.1, 0.2], [0.3, 0.4]]
            ids = ["id1", "id2"]

            ok, err = store.upsert_document_chunks(
                knowledge_base_id=1,
                document_id=1,
                chunks=chunks,
                embeddings=embeddings,
                chunk_ids=ids
            )
            assert ok is True
            assert err is None

    def test_upsert_document_chunks_length_mismatch(self):
        """Test upsert with mismatched lengths."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            chunks = ["chunk1", "chunk2"]
            embeddings = [[0.1, 0.2]]  # Only 1 embedding
            ids = ["id1", "id2"]

            ok, err = store.upsert_document_chunks(
                knowledge_base_id=1,
                document_id=1,
                chunks=chunks,
                embeddings=embeddings,
                chunk_ids=ids
            )
            assert ok is False
            assert "长度不匹配" in err

    def test_upsert_document_chunks_no_chunks(self):
        """Test upsert with no chunks."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            ok, err = store.upsert_document_chunks(
                knowledge_base_id=1,
                document_id=1,
                chunks=[],
                embeddings=[],
                chunk_ids=[]
            )
            assert ok is True
            assert err is None


class TestChromaVectorStoreQuery:
    """Tests for query operations."""

    def test_query_knowledge_base_success(self):
        """Test successful knowledge base query."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.ids = ["id1", "id2"]
        mock_result.documents = [{"content": "chunk1"}, {"content": "chunk2"}]
        mock_result.distances = [0.1, 0.2]
        mock_collection.query.return_value = mock_result
        mock_client.get_collection.return_value = mock_collection

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            results, err = store.query_knowledge_base(
                knowledge_base_id=1,
                query_embedding=[0.1, 0.2],
                top_k=5
            )
            assert err is None
            assert len(results) == 2

    def test_query_knowledge_base_with_filter(self):
        """Test query with metadata filter."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.ids = ["id1"]
        mock_result.documents = [{"content": "chunk1"}]
        mock_result.distances = [0.1]
        mock_collection.query.return_value = mock_result
        mock_client.get_collection.return_value = mock_collection

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            results, err = store.query_knowledge_base(
                knowledge_base_id=1,
                query_embedding=[0.1, 0.2],
                top_k=5,
                where_filter={"document_id": {"$eq": 1}}
            )
            assert err is None

    def test_query_knowledge_base_empty_results(self):
        """Test query returning empty results."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.ids = []
        mock_result.documents = []
        mock_result.distances = []
        mock_collection.query.return_value = mock_result
        mock_client.get_collection.return_value = mock_collection

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            results, err = store.query_knowledge_base(
                knowledge_base_id=1,
                query_embedding=[0.1, 0.2],
                top_k=5
            )
            assert err is None
            assert results == []


class TestChromaVectorStoreDelete:
    """Tests for delete operations."""

    def test_delete_document_chunks_success(self):
        """Test successful chunk deletion."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_collection = MagicMock()

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            ok, err = store.delete_document_chunks(
                knowledge_base_id=1,
                document_id=1
            )
            assert ok is True
            assert err is None
            mock_collection.delete.assert_called()

    def test_delete_knowledge_base_collection_success(self):
        """Test successful collection deletion."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            ok, err = store.delete_knowledge_base_collection(1)
            assert ok is True
            assert err is None
            mock_client.delete_collection.assert_called()


class TestChromaVectorStoreGetStats:
    """Tests for get_stats method."""

    def test_get_stats_success(self):
        """Test successful stats retrieval."""
        from app.rag.vector_store import ChromaVectorStore

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10

        mock_client.get_collection.return_value = mock_collection

        with patch("chromadb.Client", return_value=mock_client):
            store = ChromaVectorStore(host="localhost", port=8000)

            result = store.get_stats(1)
            assert "chunk_count" in result
            assert result["chunk_count"] == 10
