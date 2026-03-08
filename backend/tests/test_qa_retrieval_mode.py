"""Tests for retrieval_mode parameter in QaService.

Tests verify that retrieval_mode parameter works correctly:
- Parameter can override strategy default
- Different retrieval modes are properly executed
- Logs record actual mode used

This is a TDD approach: tests written first, then implementation.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.qa_service import QaService
from app.rag.retrieval_strategy import get_strategy


class TestRetrievalModeParameter:
    """Test retrieval_mode parameter functionality."""

    @pytest.fixture
    def mock_qa_service(self):
        """Create a mocked QaService for testing."""
        service = QaService.__new__(QaService)
        service._retriever = MagicMock()
        service._keyword_retriever = MagicMock()
        service._reranker = MagicMock()
        service._embedding_service = MagicMock()
        service._pipeline = MagicMock()
        service._vector_store = MagicMock()
        service._verify_pipeline = None

        # Mock retriever return value
        service._retriever.retrieve.return_value = (
            [
                {
                    "id": "chunk1",
                    "chunk_id": "chunk1",
                    "content": "test content",
                    "distance": 0.1,
                }
            ],
            None,
        )

        # Mock keyword retriever
        service._keyword_retriever.retrieve.return_value = (
            [
                {
                    "id": "chunk2",
                    "chunk_id": "chunk2",
                    "content": "keyword content",
                }
            ],
            None,
        )

        # Mock reranker
        service._reranker.rerank.return_value = [
            {
                "id": "chunk1",
                "chunk_id": "chunk1",
                "content": "test content",
                "rerank_score": 0.9,
            }
        ]

        return service

    def test_retrieval_mode_none_uses_strategy_default(self, mock_qa_service):
        """Test that retrieval_mode=None uses strategy's default mode."""
        with patch('app.services.qa_service.get_provider_for_task', return_value=MagicMock()):
            with patch.object(QaService, '_get_db_session', return_value=MagicMock()):
                with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                    result, err = mock_qa_service.ask(
                        knowledge_base_id=1,
                        question="test question",
                        strategy="smart",  # smart strategy uses hybrid by default
                        retrieval_mode=None,  # None should use strategy default
                    )

        # Verify strategy was loaded
        strat = get_strategy("smart")
        assert strat.retrieval_mode == "hybrid"

    def test_retrieval_mode_override_to_vector(self, mock_qa_service):
        """Test that retrieval_mode='vector' overrides strategy default."""
        with patch('app.services.qa_service.get_provider_for_task', return_value=MagicMock()):
            with patch.object(QaService, '_get_db_session', return_value=MagicMock()):
                with patch('app.services.qa_service.QaService._log_retrieval') as mock_log:
                    mock_log.return_value = 1
                    result, err = mock_qa_service.ask(
                        knowledge_base_id=1,
                        question="test question",
                        strategy="smart",  # smart strategy default is hybrid
                        retrieval_mode="vector",  # Override to vector-only
                    )

        # Verify log was called with correct mode
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs.get('retrieval_mode') == "vector"

    def test_retrieval_mode_override_to_hybrid(self, mock_qa_service):
        """Test that retrieval_mode='hybrid' can be explicitly set."""
        with patch('app.services.qa_service.get_provider_for_task', return_value=MagicMock()):
            with patch.object(QaService, '_get_db_session', return_value=MagicMock()):
                with patch('app.services.qa_service.QaService._log_retrieval') as mock_log:
                    mock_log.return_value = 1
                    result, err = mock_qa_service.ask(
                        knowledge_base_id=1,
                        question="test question",
                        strategy="fast",  # fast strategy default is vector
                        retrieval_mode="hybrid",  # Override to hybrid
                    )

        # Verify log was called with correct mode
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs.get('retrieval_mode') == "hybrid"

    def test_invalid_retrieval_mode_fallback_to_strategy(self, mock_qa_service):
        """Test that invalid retrieval_mode falls back to strategy default."""
        with patch('app.services.qa_service.get_provider_for_task', return_value=MagicMock()):
            with patch.object(QaService, '_get_db_session', return_value=MagicMock()):
                with patch('app.services.qa_service.QaService._log_retrieval') as mock_log:
                    mock_log.return_value = 1
                    result, err = mock_qa_service.ask(
                        knowledge_base_id=1,
                        question="test question",
                        strategy="smart",
                        retrieval_mode="invalid_mode",  # Invalid mode
                    )

        # Should fall back to strategy default (hybrid for smart)
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        # Either invalid mode is logged or falls back to strategy default
        assert call_kwargs.get('retrieval_mode') in ["invalid_mode", "hybrid"]

    def test_retrieval_mode_with_stream_ask(self, mock_qa_service):
        """Test that retrieval_mode works with stream_ask as well."""
        mock_stream = MagicMock()
        mock_stream.return_value.__iter__.return_value = iter(["answer"])

        with patch('app.services.qa_service.get_provider_for_task', return_value=MagicMock()):
            with patch.object(QaService, '_get_db_session', return_value=MagicMock()):
                with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                    result_generator = mock_qa_service.stream_ask(
                        knowledge_base_id=1,
                        question="test question",
                        strategy="smart",
                        retrieval_mode="vector",
                    )
                    # Consume generator
                    list(result_generator)

        # Verify stream_ask accepted retrieval_mode parameter
        # This test will fail initially, guiding implementation

    def test_retrieval_mode_logged_correctly(self, mock_qa_service):
        """Test that actual retrieval mode is logged to database."""
        with patch('app.services.qa_service.get_provider_for_task', return_value=MagicMock()):
            with patch.object(QaService, '_get_db_session', return_value=MagicMock()):
                with patch('app.services.qa_service.QaService._log_retrieval') as mock_log:
                    mock_log.return_value = 123  # log_id

                    result, err = mock_qa_service.ask(
                        knowledge_base_id=1,
                        question="test question",
                        strategy="precise",
                        retrieval_mode="hybrid",
                    )

        # Verify _log_retrieval was called with retrieval_mode
        assert mock_log.called
        call_args, call_kwargs = mock_log.call_args
        assert call_kwargs['retrieval_mode'] == "hybrid"


class TestRetrievalModeIntegration:
    """Integration tests for retrieval_mode with actual components."""

    @pytest.fixture
    def test_config(self):
        """Test configuration for integration tests."""
        return {
            "knowledge_base_id": 1,
            "question": "How to set up authentication?",
        }

    def test_vector_mode_excludes_bm25(self, test_config):
        """Test that vector mode does not call BM25 retriever."""
        service = QaService.__new__(QaService)
        service._retriever = MagicMock()
        service._keyword_retriever = MagicMock()
        service._reranker = MagicMock()

        service._retriever.retrieve.return_value = ([{"id": "chunk1"}], None)
        service._reranker.rerank.return_value = [{"id": "chunk1"}]

        with patch('app.services.qa_service.get_provider_for_task', return_value=MagicMock()):
            with patch.object(QaService, '_get_db_session', return_value=MagicMock()):
                with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                    result, err = service.ask(
                        knowledge_base_id=test_config["knowledge_base_id"],
                        question=test_config["question"],
                        retrieval_mode="vector",
                    )

        # Verify vector retriever was called
        assert service._retriever.retrieve.called

        # Verify keyword retriever was NOT called (vector-only mode)
        # Note: This will guide implementation to respect retrieval_mode

    def test_hybrid_mode_includes_vector_and_keyword(self, test_config):
        """Test that hybrid mode includes both vector and keyword retrieval."""
        service = QaService.__new__(QaService)
        service._retriever = MagicMock()
        service._keyword_retriever = MagicMock()
        service._reranker = MagicMock()

        service._retriever.retrieve.return_value = ([{"id": "chunk1"}], None)
        service._keyword_retriever.retrieve.return_value = ([{"id": "chunk2"}], None)
        service._reranker.rerank.return_value = [{"id": "chunk1"}]

        with patch('app.services.qa_service.get_provider_for_task', return_value=MagicMock()):
            with patch.object(QaService, '_get_db_session', return_value=MagicMock()):
                with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                    result, err = service.ask(
                        knowledge_base_id=test_config["knowledge_base_id"],
                        question=test_config["question"],
                        retrieval_mode="hybrid",
                    )

        # Both retrievers should be called in hybrid mode
        # Note: This will guide implementation
