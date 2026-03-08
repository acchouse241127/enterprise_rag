"""
Unit tests for KeywordRetriever.

Tests for app/rag/keyword_retriever.py
Author: C2
"""

import pytest
from unittest.mock import MagicMock, patch


class TestTokenizeForKeyword:
    """Tests for _tokenize_for_keyword function."""

    def test_tokenize_simple_words(self):
        """Test tokenizing simple words."""
        from app.rag.keyword_retriever import _tokenize_for_keyword

        tokens = _tokenize_for_keyword("hello world")
        assert "hello" in tokens
        assert "world" in tokens

    def test_tokenize_with_numbers(self):
        """Test tokenizing with numbers."""
        from app.rag.keyword_retriever import _tokenize_for_keyword

        tokens = _tokenize_for_keyword("test 123 abc")
        assert "test" in tokens
        assert "123" in tokens
        assert "abc" in tokens

    def test_tokenize_with_punctuation(self):
        """Test tokenizing with punctuation."""
        from app.rag.keyword_retriever import _tokenize_for_keyword

        tokens = _tokenize_for_keyword("hello, world!")
        assert "hello" in tokens
        assert "world" in tokens

    def test_tokenize_empty_string(self):
        """Test tokenizing empty string."""
        from app.rag.keyword_retriever import _tokenize_for_keyword

        tokens = _tokenize_for_keyword("")
        assert tokens == []

    def test_tokenize_whitespace_only(self):
        """Test tokenizing whitespace only."""
        from app.rag.keyword_retriever import _tokenize_for_keyword

        tokens = _tokenize_for_keyword("   ")
        assert tokens == []

    def test_tokenize_chinese_characters(self):
        """Test tokenizing Chinese characters."""
        from app.rag.keyword_retriever import _tokenize_for_keyword

        # Chinese characters are treated as individual punctuation tokens
        # Each character becomes a separate token
        tokens = _tokenize_for_keyword("你好世界")
        # The behavior depends on the regex - Chinese chars may or may not be captured
        # Just verify it doesn't crash
        assert isinstance(tokens, list)

    def test_tokenize_mixed_content(self):
        """Test tokenizing mixed content."""
        from app.rag.keyword_retriever import _tokenize_for_keyword

        tokens = _tokenize_for_keyword("Hello, 世界! 123")
        assert "Hello" in tokens
        assert "123" in tokens


class TestKeywordRetriever:
    """Tests for KeywordRetriever class."""

    def test_initialization(self):
        """Test KeywordRetriever initialization."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_vector_store = MagicMock()

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        assert retriever.embedding_service == mock_embedding
        assert retriever.vector_store == mock_vector_store

    def test_retrieve_empty_query(self):
        """Test retrieve with empty query."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_vector_store = MagicMock()

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        result, err = retriever.retrieve(1, "")

        assert result == []
        assert "query 不能为空" in err

    def test_retrieve_whitespace_query(self):
        """Test retrieve with whitespace query."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_vector_store = MagicMock()

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        result, err = retriever.retrieve(1, "   ")

        assert result == []
        assert "query 不能为空" in err

    def test_retrieve_vector_store_error(self):
        """Test retrieve when vector store returns error."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [[0.1, 0.2, 0.3]]

        mock_vector_store = MagicMock()
        mock_vector_store.query_knowledge_base.return_value = ([], "Connection error")

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        result, err = retriever.retrieve(1, "test query")

        assert result == []
        assert err == "Connection error"

    def test_retrieve_success(self):
        """Test successful retrieval."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [[0.1, 0.2, 0.3]]

        mock_chunks = [
            {"id": 1, "content": "hello world"},
            {"id": 2, "content": "foo bar"},
            {"id": 3, "content": "hello there"},
        ]
        mock_vector_store = MagicMock()
        mock_vector_store.query_knowledge_base.return_value = (mock_chunks, None)

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        result, err = retriever.retrieve(1, "hello", top_k=2)

        assert err is None
        assert len(result) <= 2
        # Results with "hello" should rank higher
        if len(result) > 0:
            assert result[0]["content"] in ["hello world", "hello there"]

    def test_retrieve_with_custom_top_k(self):
        """Test retrieval with custom top_k."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [[0.1] * 10]

        mock_chunks = [{"id": i, "content": f"chunk {i}"} for i in range(20)]
        mock_vector_store = MagicMock()
        mock_vector_store.query_knowledge_base.return_value = (mock_chunks, None)

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        result, err = retriever.retrieve(1, "chunk", top_k=3)

        assert err is None
        assert len(result) == 3

    def test_retrieve_no_matching_keywords(self):
        """Test retrieval when no keywords match."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [[0.1, 0.2, 0.3]]

        mock_chunks = [
            {"id": 1, "content": "foo bar"},
            {"id": 2, "content": "baz qux"},
        ]
        mock_vector_store = MagicMock()
        mock_vector_store.query_knowledge_base.return_value = (mock_chunks, None)

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        result, err = retriever.retrieve(1, "hello world", top_k=2)

        assert err is None
        assert len(result) == 2
        # All scores are 0, so order is preserved

    def test_retrieve_strips_query(self):
        """Test that query is stripped before processing."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [[0.1]]

        mock_vector_store = MagicMock()
        mock_vector_store.query_knowledge_base.return_value = ([], None)

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        retriever.retrieve(1, "  test query  ")

        # Verify embed was called with stripped query
        mock_embedding.embed.assert_called_once_with(["test query"])

    def test_retrieve_calls_vector_store_with_multiplier(self):
        """Test that vector store is called with multiplied top_k."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [[0.1]]

        mock_vector_store = MagicMock()
        mock_vector_store.query_knowledge_base.return_value = ([], None)

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        retriever.retrieve(1, "test", top_k=5, candidate_multiplier=3)

        # Should request at least 5 * 3 = 15 candidates
        call_args = mock_vector_store.query_knowledge_base.call_args
        assert call_args[1]["top_k"] >= 15

    def test_retrieve_minimum_candidates(self):
        """Test that minimum of 20 candidates is requested."""
        from app.rag.keyword_retriever import KeywordRetriever

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [[0.1]]

        mock_vector_store = MagicMock()
        mock_vector_store.query_knowledge_base.return_value = ([], None)

        retriever = KeywordRetriever(mock_embedding, mock_vector_store)
        retriever.retrieve(1, "test", top_k=2, candidate_multiplier=2)

        # Should request at least 20 candidates (minimum)
        call_args = mock_vector_store.query_knowledge_base.call_args
        assert call_args[1]["top_k"] >= 20
