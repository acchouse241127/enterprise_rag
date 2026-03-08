"""
Unit tests for Reranker service.

Tests for app/rag/reranker.py
Author: C2
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestBgeRerankerService:
    """Tests for BgeRerankerService class."""

    def test_initialization(self):
        """Test reranker initialization."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()
        assert reranker.model_name == "BAAI/bge-reranker-v2-m3"
        assert reranker._model is None
        assert reranker._load_error is None

    def test_initialization_custom_model(self):
        """Test reranker with custom model name."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService(model_name="custom/model")
        assert reranker.model_name == "custom/model"

    def test_get_model_lazy_loading(self):
        """Test that model is loaded lazily."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()

        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            import sys
            mock_cross_encoder = MagicMock()
            sys.modules["sentence_transformers"].CrossEncoder = mock_cross_encoder

            # First call should load model
            model = reranker._get_model()
            mock_cross_encoder.assert_called_once_with("BAAI/bge-reranker-v2-m3")

            # Second call should return cached model
            model2 = reranker._get_model()
            mock_cross_encoder.assert_called_once()  # Not called again

    def test_get_model_caches_load_error(self):
        """Test that load error is cached."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()

        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            import sys
            sys.modules["sentence_transformers"].CrossEncoder = MagicMock(
                side_effect=ImportError("No module")
            )

            # First call should raise and cache error
            with pytest.raises(RuntimeError) as exc_info:
                reranker._get_model()
            assert "加载 Reranker 模型失败" in str(exc_info.value)

            # Second call should raise cached error without trying to load
            with pytest.raises(RuntimeError):
                reranker._get_model()

    def test_fallback_score_basic(self):
        """Test fallback score calculation."""
        from app.rag.reranker import BgeRerankerService

        # Exact match
        score = BgeRerankerService._fallback_score("hello world", "hello world")
        assert score > 0

        # No match
        score = BgeRerankerService._fallback_score("apple", "banana")
        assert score == 0.0

        # Partial match
        score = BgeRerankerService._fallback_score("hello world", "hello there")
        assert 0 < score < 1

    def test_fallback_score_empty_query(self):
        """Test fallback score with empty query."""
        from app.rag.reranker import BgeRerankerService

        score = BgeRerankerService._fallback_score("", "some content")
        assert score == 0.0

    def test_fallback_score_empty_content(self):
        """Test fallback score with empty content."""
        from app.rag.reranker import BgeRerankerService

        score = BgeRerankerService._fallback_score("some query", "")
        assert score == 0.0

    def test_fallback_score_whitespace_only(self):
        """Test fallback score with whitespace only."""
        from app.rag.reranker import BgeRerankerService

        score = BgeRerankerService._fallback_score("   ", "   ")
        assert score == 0.0

    def test_rerank_empty_chunks(self):
        """Test rerank with empty chunk list."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()
        result = reranker.rerank("query", [], top_n=5)
        assert result == []

    def test_rerank_zero_top_n(self):
        """Test rerank with top_n=0."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()
        chunks = [{"content": "test"}]
        result = reranker.rerank("query", chunks, top_n=0)
        assert result == []

    def test_rerank_negative_top_n(self):
        """Test rerank with negative top_n."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()
        chunks = [{"content": "test"}]
        result = reranker.rerank("query", chunks, top_n=-1)
        assert result == []

    def test_rerank_with_model(self):
        """Test rerank with model successfully loaded."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()

        chunks = [
            {"id": 1, "content": "First chunk"},
            {"id": 2, "content": "Second chunk"},
            {"id": 3, "content": "Third chunk"},
        ]

        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9, 0.5, 0.7]

        with patch.object(reranker, "_get_model", return_value=mock_model):
            result = reranker.rerank("query", chunks, top_n=2)

            # Should return top 2 sorted by score
            assert len(result) == 2
            # First should have highest score (0.9)
            assert result[0]["id"] == 1
            assert result[0]["rerank_score"] == 0.9

    def test_rerank_model_returns_all_chunks_when_top_n_larger(self):
        """Test rerank when top_n is larger than chunk count."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()

        chunks = [
            {"id": 1, "content": "First"},
            {"id": 2, "content": "Second"},
        ]

        mock_model = MagicMock()
        mock_model.predict.return_value = [0.5, 0.6]

        with patch.object(reranker, "_get_model", return_value=mock_model):
            result = reranker.rerank("query", chunks, top_n=10)

            # Should return all chunks
            assert len(result) == 2

    def test_rerank_fallback_on_model_error(self):
        """Test rerank falls back to lexical when model fails."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()

        chunks = [
            {"id": 1, "content": "apple banana"},
            {"id": 2, "content": "orange grape"},
        ]

        with patch.object(reranker, "_get_model", side_effect=RuntimeError("Model failed")):
            result = reranker.rerank("apple", chunks, top_n=2)

            # Should use fallback scoring
            assert len(result) == 2
            # First result should contain "apple" which matches query
            assert result[0]["id"] == 1

    def test_rerank_preserves_original_chunk_data(self):
        """Test that rerank preserves original chunk fields."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()

        chunks = [
            {"id": 1, "content": "test", "metadata": {"key": "value"}},
        ]

        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9]

        with patch.object(reranker, "_get_model", return_value=mock_model):
            result = reranker.rerank("query", chunks, top_n=1)

            assert result[0]["id"] == 1
            assert result[0]["content"] == "test"
            assert result[0]["metadata"] == {"key": "value"}
            assert "rerank_score" in result[0]

    def test_rerank_handles_missing_content(self):
        """Test rerank handles chunks without content field."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()

        chunks = [
            {"id": 1},  # No content
        ]

        mock_model = MagicMock()
        mock_model.predict.return_value = [0.5]

        with patch.object(reranker, "_get_model", return_value=mock_model):
            result = reranker.rerank("query", chunks, top_n=1)

            assert len(result) == 1
            assert result[0]["id"] == 1

    def test_rerank_sorts_descending(self):
        """Test that rerank sorts by score descending."""
        from app.rag.reranker import BgeRerankerService

        reranker = BgeRerankerService()

        chunks = [
            {"id": 1, "content": "low"},
            {"id": 2, "content": "high"},
            {"id": 3, "content": "medium"},
        ]

        mock_model = MagicMock()
        mock_model.predict.return_value = [0.3, 0.9, 0.6]

        with patch.object(reranker, "_get_model", return_value=mock_model):
            result = reranker.rerank("query", chunks, top_n=3)

            assert result[0]["id"] == 2  # 0.9
            assert result[1]["id"] == 3  # 0.6
            assert result[2]["id"] == 1  # 0.3
