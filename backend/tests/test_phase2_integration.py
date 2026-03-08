"""Integration tests for Phase 2 components.

Tests verify that Phase 2 components work correctly:
with QaService integration.

Author: C2
Date: 2026-03-03
"""

import pytest
from unittest.mock import MagicMock, patch

from app.config import settings
from app.services.qa_service import QaService
from app.rag.self_query_retriever import SelfQueryRetriever
from app.rag.splade_retriever import SpladeRetriever
from app.rag.retrieval_orchestrator import RetrievalOrchestrator
from app.cache.query_cache import QueryCacheService
from app.security.pii_anonymizer import PiiAnonymizer
from app.content.forbidden_word_service import ForbiddenWordFilter


class TestPhase2Integration:
    """Integration tests for Phase 2 components."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM provider."""
        return MagicMock()

    @pytest.fixture
    def mock_retriever(self):
        """Mock vector retriever."""
        retriever = MagicMock()
        retriever.retrieve = MagicMock(return_value=(
            [{"chunk_id": 1, "content": "test content", "distance": 0.1}],
            None,
        ))
        return retriever
    @pytest.fixture
    def mock_reranker(self):
        """Mock reranker."""
        reranker = MagicMock()
        reranker.rerank = MagicMock(return_value=[
            {"chunk_id": 1, "content": "test content", "rerank_score": 0.9}
        ])
        return reranker
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        return MagicMock()
    @pytest.fixture
    def mock_pii_anonymizer(self):
        """Mock PII anonymizer."""
        anonymizer = MagicMock()
        anonymizer.anonymize = MagicMock(
            return_value=MagicMock(
                original_text="test",
                anonymized_text="test",
                detected_pii=[],
                pii_map={},
            )
        )
        return anonymizer
    @pytest.fixture
    def mock_forbidden_filter(self):
        """Mock forbidden word filter."""
        filter = MagicMock()
        filter.filter = MagicMock(
            return_value=MagicMock(
                original_text="test",
                filtered_text="test",
                detected_words=[],
                action_taken="none",
            )
        )
        return filter

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock retrieval orchestrator."""
        orchestrator = MagicMock()
        orchestrator.retrieve = MagicMock(return_value=(
            [{"chunk_id": 1, "content": "test", "distance": 0.1}],
            MagicMock(level="L0_NORMAL", reason="Success"),
        ))
        return orchestrator
    @pytest.fixture
    def mock_self_query(self):
        """Mock self-query retriever."""
        return MagicMock()
    @pytest.fixture
    def mock_splade(self):
        """Mock SPLADE retriever."""
        return MagicMock()
    @patch("app.services.qa_service.QaService._initialize_phase2_components")
    def _mock_initialize(self):
        """Mock Phase 2 initialization."""
        pass
    def test_qa_service_phase2_disabled(self):
        """Test Phase 2 components are disabled by default."""
        with patch.object(settings) as mock_settings:
            mock_settings.self_query_enabled = False
            mock_settings.splade_enabled = False
            mock_settings.cache_enabled = False
            mock_settings.pii_anonymization_enabled = False
            mock_settings.forbidden_words_enabled = False

        qa = QaService()
        assert qa._self_query_retriever is None
        assert qa._splade_retriever is None
        assert qa._cache_service is None
        assert qa._pii_anonymizer is None
        assert qa._forbidden_word_filter is None
        assert qa._initialized is False
        assert qa._retrieval_orchestrator is None

    def test_qa_service_phase2_enabled(self, mock_settings):
        """Test Phase 2 components are enabled by default."""
        mock_settings.self_query_enabled = True
        mock_settings.splade_enabled = True
        mock_settings.cache_enabled = True
        mock_settings.pii_anonymization_enabled = True
        mock_settings.forbidden_words_enabled = True
        with patch.object(settings, return_value=mock_settings):
            qa = QaService()
            assert qa._self_query_retriever is not None
            assert qa._splade_retriever is not None
            assert qa._cache_service is not None
            assert qa._pii_anonymizer is not None
            assert qa._forbidden_word_filter is not None
            assert qa._initialized is True
            assert qa._retrieval_orchestrator is not None
    @patch("app.services.qa_service.QaService._get_llm_provider_for_self_query")
    @patch("app.services.qa_service.QaService._get_db_session")
    def test_cache_integration(self, mock_cache_service, mock_llm, mock_retriever, mock_reranker, mock_pii_anonymizer, mock_forbidden_filter, mock_orchestrator):
        """Test cache integration with Phase 2 components."""
        # Setup cache hit
        mock_cache_service.get = MagicMock(return_value={
            "answer": "cached answer",
            "citations": [],
            "cache_type": "exact"
        })
        qa = QaService()
        qa._cache_service = mock_cache_service
        qa._pii_anonymizer = mock_pii_anonymizer
        qa._forbidden_word_filter = mock_forbidden_filter
        qa._retrieval_orchestrator = mock_orchestrator
        result, err = qa.ask(
            knowledge_base_id=1,
            question="test question"
        )
        # Verify cache was checked
        mock_cache_service.get.assert_called_once_with(1, "test question")
        # Verify PII was NOT processed (cache miss)
        assert result is not None
        assert result["answer"] == "cached answer"
        # Verify LLM was not called (cache hit)
        mock_llm.generate.assert_not_called()
    @patch("app.services.qa_service.QaService._get_llm_provider_for_self_query")
    @patch("app.services.qa_service.QaService._get_db_session")
    def test_pii_anonymization_integration(self, mock_pii_anonymizer, mock_retriever, mock_reranker, mock_cache_service):
        """Test PII anonymization with Phase 2 components."""
        # Setup PII anonymization
        mock_pii_anonymizer.anonymize = MagicMock(
            return_value=MagicMock(
                original_text="My phone is 13812345678",
                anonymized_text="My phone is <PHONE_0001>",
                detected_pii=[{"type": "phone", "value": "13812345678"}],
                pii_map={"<PHONE_0001>": "13812345678"},
            )
        )
        qa = QaService()
        qa._cache_service = mock_cache_service
        qa._pii_anonymizer = mock_pii_anonymizer
        qa._forbidden_word_filter = mock_forbidden_filter
        qa._retrieval_orchestrator = mock_orchestrator
        result, err = qa.ask(
            knowledge_base_id=1,
            question="My phone is 13812345678"
        )
        # Verify PII was processed
        mock_pii_anonymizer.anonymize.assert_called_once_with("My phone is 13812345678")
        # Verify PII was restored in final answer
        mock_pii_anonymizer.restore = MagicMock(return_value="final answer")
        # Verify retriever was called
        mock_retriever.retrieve.assert_called_once()
        assert result is not None
        assert result["answer"] == "final answer"
    @patch("app.services.qa_service.QaService._get_llm_provider_for_self_query")
    @patch("app.services.qa_service.QaService._get_db_session")
    def test_forbidden_word_filter(self, mock_forbidden_filter, mock_retriever, mock_reranker, mock_cache_service, mock_pii_anonymizer):
        """Test forbidden word filter with Phase 2 components."""
        # Setup forbidden word filter
        mock_forbidden_filter.filter = MagicMock(
            return_value=MagicMock(
                original_text="这是最佳的产品",
                filtered_text="这是优秀的产品",
                detected_words=[{"word": "最佳", "replacement": "优秀"}],
                action_taken="replace",
            )
        )
        qa = QaService()
        qa._cache_service = mock_cache_service
        qa._pii_anonymizer = mock_pii_anonymizer
        qa._forbidden_word_filter = mock_forbidden_filter
        qa._retrieval_orchestrator = mock_orchestrator
        result, err = qa.ask(
            knowledge_base_id=1,
            question="这是最佳的产品"
        )
        # Verify forbidden word filter was called
        mock_forbidden_filter.filter.assert_called_once_with("这是最佳的产品")
        # Verify answer is generated
        mock_retriever.retrieve.assert_called_once()
        assert result is not None
        assert result["answer"] == "这是优秀的产品"
        assert "最佳" not in result["answer"]
    @patch("app.services.qa_service.QaService._get_llm_provider_for_self_query")
    @patch("app.services.qa_service.QaService._get_db_session")
    def test_degradation_strategy(self, mock_orchestrator):
        """Test degradation strategy with Phase 2 components."""
        # Setup degradation
        mock_orchestrator.retrieve = MagicMock(return_value=(
            None,
            MagicMock(level="L1_VECTOR_timeout", reason="Vector timeout", fallback_used="bm25")
        ))
        qa = QaService()
        qa._cache_service = mock_cache_service
        qa._pii_anonymizer = mock_pii_anonymizer
        qa._forbidden_word_filter = mock_forbidden_filter
        qa._retrieval_orchestrator = mock_orchestrator
        result, err = qa.ask(
            knowledge_base_id=1,
            question="test question"
        )
        # Verify degradation was triggered
        mock_orchestrator.retrieve.assert_called_once()
        # Verify fallback was called
        mock_retriever.retrieve.assert_called_once()
        assert result is not None
        # Check degradation info
        assert result.get("degradation_info") is not None
        deg_info = result["degradation_info"]
        assert deg_info["level"] == "L1"
        assert "bm25" in deg_info["fallback_used"]
    @patch("app.services.qa_service.QaService._get_llm_provider_for_self_query")
    @patch("app.services.qa_service.QaService._get_db_session")
    def test_self_query_enabled(self, mock_self_query, mock_retriever, mock_reranker, mock_cache_service, mock_pii_anonymizer, mock_forbidden_filter, mock_orchestrator):
        """Test self-query retriever when enabled."""
        # Setup self-query
        mock_self_query.retrieve = MagicMock(return_value=(
            [{"chunk_id": 1, "content": "filtered content", "distance": 0.1}],
            None,
        ))
        qa = QaService()
        qa._cache_service = mock_cache_service
        qa._pii_anonymizer = mock_pii_anonymizer
        qa._forbidden_word_filter = mock_forbidden_filter
        qa._retrieval_orchestrator = mock_orchestrator
        qa._self_query_retriever = mock_self_query
        result, err = qa.ask(
            knowledge_base_id=1,
            question="2024年的财务报告"
        )
        # Verify self-query was called
        mock_self_query.retrieve.assert_called_once_with(1, "2024年的财务报告")
        # Verify LLM was NOT called
        mock_llm.generate.assert_not_called()
        # Verify base retriever was called
        mock_retriever.retrieve.assert_called_once()
