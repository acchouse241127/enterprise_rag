"""Comprehensive tests for RetrievalOrchestrator module.

Tests cover:
- DegradationLevel and DegradationInfo
- HealthChecker functionality
- RetrievalOrchestrator multi-level fallback strategy
- Timeout handling
- Fallback scenarios
"""

import pytest
import time
import threading
from unittest.mock import MagicMock, patch

from app.rag.retrieval_orchestrator import (
    DegradationLevel,
    DegradationInfo,
    HealthChecker,
    RetrievalOrchestrator,
    create_orchestrator,
)


class TestDegradationLevel:
    """Tests for DegradationLevel enum."""

    def test_degradation_level_values(self):
        """Test DegradationLevel enum values."""
        assert DegradationLevel.L0_NORMAL == "L0_NORMAL"
        assert DegradationLevel.L1_VECTOR_TIMEOUT == "L1_VECTOR_TIMEOUT"
        assert DegradationLevel.L2_VECTOR_UNAVAILABLE == "L2_VECTOR_UNAVAILABLE"
        assert DegradationLevel.L3_ALL_FAILED == "L3_ALL_FAILED"


class TestDegradationInfo:
    """Tests for DegradationInfo dataclass."""

    def test_degradation_info_creation(self):
        """Test creating DegradationInfo instance."""
        info = DegradationInfo(
            level=DegradationLevel.L0_NORMAL,
            reason="Success",
            fallback_used=None,
        )
        assert info.level == DegradationLevel.L0_NORMAL
        assert info.reason == "Success"
        assert info.fallback_used is None
        assert isinstance(info.timestamp, float)

    def test_degradation_info_with_fallback(self):
        """Test DegradationInfo with fallback."""
        info = DegradationInfo(
            level=DegradationLevel.L1_VECTOR_TIMEOUT,
            reason="Vector timeout",
            fallback_used="bm25",
        )
        assert info.fallback_used == "bm25"

    def test_degradation_info_to_dict(self):
        """Test converting DegradationInfo to dict."""
        info = DegradationInfo(
            level=DegradationLevel.L0_NORMAL,
            reason="Test reason",
            fallback_used="bm25",
            timestamp=1234567890.0,
        )
        result = info.to_dict()
        assert result["level"] == "L0_NORMAL"
        assert result["reason"] == "Test reason"
        assert result["fallback_used"] == "bm25"
        assert result["timestamp"] == 1234567890.0

    def test_degradation_info_from_dict(self):
        """Test creating DegradationInfo from dict."""
        data = {
            "level": "L1_VECTOR_TIMEOUT",
            "reason": "Timeout",
            "fallback_used": "bm25",
            "timestamp": 1234567890.0,
        }
        info = DegradationInfo.from_dict(data)
        assert info.level == DegradationLevel.L1_VECTOR_TIMEOUT
        assert info.reason == "Timeout"
        assert info.fallback_used == "bm25"
        assert info.timestamp == 1234567890.0

    def test_degradation_info_from_dict_default_timestamp(self):
        """Test DegradationInfo.from_dict with default timestamp."""
        data = {
            "level": "L0_NORMAL",
            "reason": "Success",
            "fallback_used": None,
        }
        info = DegradationInfo.from_dict(data)
        assert isinstance(info.timestamp, float)
        assert info.timestamp > 0


class TestHealthChecker:
    """Tests for HealthChecker."""

    def test_health_checker_init_defaults(self):
        """Test HealthChecker initialization with defaults."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.health_check_interval_seconds = 60
            checker = HealthChecker()
            assert checker._vector_retriever is None
            assert checker._is_healthy is True
            assert checker._last_check_time == 0
            assert checker._lock is not None
            assert checker._check_interval == 60

    def test_health_checker_init_with_retriever(self):
        """Test HealthChecker initialization with retriever."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.health_check_interval_seconds = 60
            mock_retriever = MagicMock()
            checker = HealthChecker(vector_retriever=mock_retriever, check_interval_seconds=60)
            assert checker._vector_retriever is mock_retriever
            assert checker._check_interval == 60

    def test_health_checker_is_healthy_none_retriever(self):
        """Test is_healthy when retriever is None."""
        checker = HealthChecker()
        assert checker.is_healthy() is False

    def test_health_checker_is_healthy_no_health_check_method(self):
        """Test is_healthy when retriever has no health_check method."""
        mock_retriever = MagicMock(spec=[])
        checker = HealthChecker(vector_retriever=mock_retriever)
        assert checker.is_healthy() is True

    def test_health_checker_is_healthy_with_health_check_true(self):
        """Test is_healthy when health_check returns True."""
        mock_retriever = MagicMock()
        mock_retriever.health_check.return_value = True
        checker = HealthChecker(vector_retriever=mock_retriever)
        assert checker.is_healthy() is True

    def test_health_checker_is_healthy_with_health_check_false(self):
        """Test is_healthy when health_check returns False."""
        mock_retriever = MagicMock()
        mock_retriever.health_check.return_value = False
        checker = HealthChecker(vector_retriever=mock_retriever)
        assert checker.is_healthy() is False

    def test_health_checker_is_healthy_exception(self):
        """Test is_healthy when health_check raises exception."""
        mock_retriever = MagicMock()
        mock_retriever.health_check.side_effect = Exception("Health check failed")
        checker = HealthChecker(vector_retriever=mock_retriever)
        assert checker.is_healthy() is False

    def test_health_checker_check_and_update_first_time(self):
        """Test check_and_update on first call."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.health_check_interval_seconds = 60
            mock_retriever = MagicMock()
            mock_retriever.health_check.return_value = True
            checker = HealthChecker(vector_retriever=mock_retriever, check_interval_seconds=60)
            result = checker.check_and_update()
            assert result is True
            assert checker._is_healthy is True
            assert checker._last_check_time > 0

    def test_health_checker_check_and_update_within_interval(self):
        """Test check_and_update within check interval."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.health_check_interval_seconds = 60
            checker = HealthChecker(check_interval_seconds=60)
            checker._is_healthy = True
            checker._last_check_time = time.time()
            result = checker.check_and_update()
            assert result is True  # Should return cached value

    def test_health_checker_check_and_update_after_interval(self):
        """Test check_and_update after check interval."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.health_check_interval_seconds = 0
            mock_retriever = MagicMock()
            mock_retriever.health_check.return_value = False
            checker = HealthChecker(
                vector_retriever=mock_retriever,
                check_interval_seconds=0
            )
            checker._is_healthy = True
            checker._last_check_time = 0
            result = checker.check_and_update()
            assert result is False
            assert checker._is_healthy is False


class TestRetrievalOrchestrator:
    """Tests for RetrievalOrchestrator."""

    def test_orchestrator_init_defaults(self):
        """Test RetrievalOrchestrator initialization with defaults."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            orchestrator = RetrievalOrchestrator()
            assert orchestrator._vector_retriever is None
            assert orchestrator._bm25_retriever is None
            assert orchestrator.timeout_ms == 5000
            assert orchestrator.fallback_enabled is True
            assert orchestrator._health_checker is not None

    def test_orchestrator_init_with_params(self):
        """Test RetrievalOrchestrator initialization with parameters."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.health_check_interval_seconds = 60
            mock_vector = MagicMock()
            mock_bm25 = MagicMock()
            
            orchestrator = RetrievalOrchestrator(
                vector_retriever=mock_vector,
                bm25_retriever=mock_bm25,
                timeout_ms=3000,
                fallback_enabled=False,
            )
            assert orchestrator._vector_retriever is mock_vector
            assert orchestrator._bm25_retriever is mock_bm25
            assert orchestrator.timeout_ms == 3000
            assert orchestrator.fallback_enabled is False

    def test_retrieve_with_timeout_none_retriever(self):
        """Test _retrieve_with_timeout with None retriever."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            orchestrator = RetrievalOrchestrator()
            
            result, error = orchestrator._retrieve_with_timeout(
                None, kb_id=1, query="test", top_k=5
            )
            assert result is None
            assert error == "Retriever not available"

    def test_retrieve_with_timeout_success(self):
        """Test _retrieve_with_timeout with successful retrieval."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = (["chunk1", "chunk2"], None)
        
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            orchestrator = RetrievalOrchestrator()
            
            result, error = orchestrator._retrieve_with_timeout(
                mock_retriever, kb_id=1, query="test", top_k=5
            )
            assert result == ["chunk1", "chunk2"]
            assert error is None

    def test_retrieve_with_timeout_exception(self):
        """Test _retrieve_with_timeout with exception."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = Exception("Retrieval failed")
        
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            orchestrator = RetrievalOrchestrator()
            
            result, error = orchestrator._retrieve_with_timeout(
                mock_retriever, kb_id=1, query="test", top_k=5
            )
            assert result is None
            assert "Retrieval failed" in error

    def test_retrieve_with_timeout_actual_timeout(self):
        """Test _retrieve_with_timeout with actual timeout."""
        def slow_retrieve(kb_id, query, top_k):
            time.sleep(2)  # Sleep longer than timeout
            return (["chunk"], None)
        
        mock_retriever = MagicMock()
        mock_retriever.retrieve = slow_retrieve
        
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 100  # 100ms timeout
            orchestrator = RetrievalOrchestrator()
            
            result, error = orchestrator._retrieve_with_timeout(
                mock_retriever, kb_id=1, query="test", top_k=5
            )
            assert result is None
            assert "Timeout" in error

    def test_try_bm25_fallback_none_retriever(self):
        """Test _try_bm25_fallback with None retriever."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            orchestrator = RetrievalOrchestrator()
            
            result, info = orchestrator._try_bm25_fallback(
                kb_id=1, query="test", top_k=5, reason="Test"
            )
            assert result is None
            assert info.level == DegradationLevel.L3_ALL_FAILED
            assert "BM25 fallback unavailable" in info.reason

    def test_try_bm25_fallback_success(self):
        """Test _try_bm25_fallback with successful retrieval."""
        mock_bm25 = MagicMock()
        mock_bm25.retrieve.return_value = (["chunk1", "chunk2"], None)
        
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            orchestrator = RetrievalOrchestrator(bm25_retriever=mock_bm25)
            
            result, info = orchestrator._try_bm25_fallback(
                kb_id=1, query="test", top_k=5, reason="Timeout after 5000ms"
            )
            assert result == ["chunk1", "chunk2"]
            assert info.level == DegradationLevel.L1_VECTOR_TIMEOUT
            assert info.fallback_used == "bm25"

    def test_try_bm25_fallback_returns_none(self):
        """Test _try_bm25_fallback when BM25 returns None."""
        mock_bm25 = MagicMock()
        mock_bm25.retrieve.return_value = None
        
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            orchestrator = RetrievalOrchestrator(bm25_retriever=mock_bm25)
            
            result, info = orchestrator._try_bm25_fallback(
                kb_id=1, query="test", top_k=5, reason="Test"
            )
            assert result is None
            assert info.level == DegradationLevel.L3_ALL_FAILED
            assert "returned None" in info.reason

    def test_try_bm25_fallback_error(self):
        """Test _try_bm25_fallback when BM25 returns error."""
        mock_bm25 = MagicMock()
        mock_bm25.retrieve.return_value = (None, "BM25 error")
        
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            orchestrator = RetrievalOrchestrator(bm25_retriever=mock_bm25)
            
            result, info = orchestrator._try_bm25_fallback(
                kb_id=1, query="test", top_k=5, reason="Test"
            )
            assert result is None
            assert info.level == DegradationLevel.L3_ALL_FAILED
            assert "BM25 retrieval failed" in info.reason

    def test_try_bm25_fallback_exception(self):
        """Test _try_bm25_fallback when BM25 raises exception."""
        mock_bm25 = MagicMock()
        mock_bm25.retrieve.side_effect = Exception("BM25 exception")
        
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            orchestrator = RetrievalOrchestrator(bm25_retriever=mock_bm25)
            
            result, info = orchestrator._try_bm25_fallback(
                kb_id=1, query="test", top_k=5, reason="Test"
            )
            assert result is None
            assert info.level == DegradationLevel.L3_ALL_FAILED
            assert "BM25 fallback exception" in info.reason

    def test_retrieve_normal_success(self):
        """Test retrieve with normal success."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_vector.health_check.return_value = True
            mock_vector.retrieve.return_value = (["chunk1", "chunk2"], None)
            
            orchestrator = RetrievalOrchestrator(vector_retriever=mock_vector)
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks == ["chunk1", "chunk2"]
            assert info.level == DegradationLevel.L0_NORMAL
            assert info.reason == "Success"
            assert info.fallback_used is None

    def test_retrieve_returns_empty_list(self):
        """Test retrieve when retriever returns None for chunks."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_vector.health_check.return_value = True
            mock_vector.retrieve.return_value = (None, None)
            
            orchestrator = RetrievalOrchestrator(vector_retriever=mock_vector)
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks == []  # Should convert None to []
            assert info.level == DegradationLevel.L0_NORMAL

    def test_retrieve_health_check_failed_fallback_enabled(self):
        """Test retrieve when health check fails with fallback enabled."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_vector.health_check.return_value = False
            mock_bm25 = MagicMock()
            mock_bm25.retrieve.return_value = (["bm25_chunk"], None)
            
            orchestrator = RetrievalOrchestrator(
                vector_retriever=mock_vector,
                bm25_retriever=mock_bm25,
            )
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks == ["bm25_chunk"]
            assert info.level == DegradationLevel.L2_VECTOR_UNAVAILABLE
            assert info.fallback_used == "bm25"

    def test_retrieve_health_check_failed_fallback_disabled(self):
        """Test retrieve when health check fails with fallback disabled."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = False
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_vector.health_check.return_value = False
            
            orchestrator = RetrievalOrchestrator(vector_retriever=mock_vector)
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks is None
            assert info.level == DegradationLevel.L2_VECTOR_UNAVAILABLE
            assert info.fallback_used is None

    def test_retrieve_no_vector_retriever_fallback_enabled(self):
        """Test retrieve with no vector retriever but fallback enabled."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_bm25 = MagicMock()
            mock_bm25.retrieve.return_value = (["bm25_chunk"], None)
            
            orchestrator = RetrievalOrchestrator(bm25_retriever=mock_bm25)
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks == ["bm25_chunk"]
            assert info.fallback_used == "bm25"

    def test_retrieve_no_vector_retriever_fallback_disabled(self):
        """Test retrieve with no retriever and fallback disabled."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = False
            mock_settings.health_check_interval_seconds = 60
            
            orchestrator = RetrievalOrchestrator()
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks is None
            # When no vector retriever and fallback disabled, health check fails
            assert info.level == DegradationLevel.L2_VECTOR_UNAVAILABLE
            assert "fallback disabled" in info.reason

    def test_retrieve_timeout_with_fallback(self):
        """Test retrieve with timeout and fallback."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 100
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_vector.health_check.return_value = True
            
            def slow_retrieve(kb_id, query, top_k):
                time.sleep(2)
                return (["chunk"], None)
            
            mock_vector.retrieve = slow_retrieve
            
            mock_bm25 = MagicMock()
            mock_bm25.retrieve.return_value = (["bm25_chunk"], None)
            
            orchestrator = RetrievalOrchestrator(
                vector_retriever=mock_vector,
                bm25_retriever=mock_bm25,
            )
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks == ["bm25_chunk"]
            assert info.level == DegradationLevel.L1_VECTOR_TIMEOUT
            assert info.fallback_used == "bm25"

    def test_retrieve_error_with_fallback(self):
        """Test retrieve with error and fallback."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_vector.health_check.return_value = True
            mock_vector.retrieve.return_value = (None, "Vector error")
            
            mock_bm25 = MagicMock()
            mock_bm25.retrieve.return_value = (["bm25_chunk"], None)
            
            orchestrator = RetrievalOrchestrator(
                vector_retriever=mock_vector,
                bm25_retriever=mock_bm25,
            )
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks == ["bm25_chunk"]
            assert info.level == DegradationLevel.L2_VECTOR_UNAVAILABLE
            assert info.fallback_used == "bm25"

    def test_retrieve_error_without_fallback(self):
        """Test retrieve with error but no fallback."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = False
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_vector.health_check.return_value = True
            mock_vector.retrieve.return_value = (None, "Vector error")
            
            orchestrator = RetrievalOrchestrator(vector_retriever=mock_vector)
            chunks, info = orchestrator.retrieve(kb_id=1, query="test")
            
            assert chunks is None
            assert info.level == DegradationLevel.L3_ALL_FAILED
            assert "Vector error" in info.reason

    def test_retrieve_custom_top_k(self):
        """Test retrieve with custom top_k."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_top_k = 5
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_vector.health_check.return_value = True
            mock_vector.retrieve.return_value = (["chunk1"], None)
            
            orchestrator = RetrievalOrchestrator(vector_retriever=mock_vector)
            chunks, info = orchestrator.retrieve(kb_id=1, query="test", top_k=10)
            
            mock_vector.retrieve.assert_called_once_with(kb_id=1, query="test", top_k=10)

    def test_update_retrievers(self):
        """Test update_retrievers method."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_bm25 = MagicMock()
            
            orchestrator = RetrievalOrchestrator()
            assert orchestrator._vector_retriever is None
            assert orchestrator._bm25_retriever is None
            
            orchestrator.update_retrievers(
                vector_retriever=mock_vector,
                bm25_retriever=mock_bm25,
            )
            
            assert orchestrator._vector_retriever is mock_vector
            assert orchestrator._bm25_retriever is mock_bm25
            assert orchestrator._health_checker._vector_retriever is mock_vector

    def test_update_retrievers_partial(self):
        """Test update_retrievers with partial update."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            
            orchestrator = RetrievalOrchestrator()
            orchestrator.update_retrievers(vector_retriever=mock_vector)
            
            assert orchestrator._vector_retriever is mock_vector
            assert orchestrator._bm25_retriever is None


class TestCreateOrchestrator:
    """Tests for create_orchestrator factory function."""

    def test_create_orchestrator_default(self):
        """Test create_orchestrator with defaults."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            orchestrator = create_orchestrator()
            assert isinstance(orchestrator, RetrievalOrchestrator)
            assert orchestrator._vector_retriever is None
            assert orchestrator._bm25_retriever is None

    def test_create_orchestrator_with_retrievers(self):
        """Test create_orchestrator with retrievers."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            mock_vector = MagicMock()
            mock_bm25 = MagicMock()
            
            orchestrator = create_orchestrator(
                vector_retriever=mock_vector,
                bm25_retriever=mock_bm25,
            )
            assert isinstance(orchestrator, RetrievalOrchestrator)
            assert orchestrator._vector_retriever is mock_vector
            assert orchestrator._bm25_retriever is mock_bm25

    def test_create_orchestrator_with_kwargs(self):
        """Test create_orchestrator with kwargs."""
        with patch('app.rag.retrieval_orchestrator.settings') as mock_settings:
            mock_settings.retrieval_timeout_ms = 5000
            mock_settings.retrieval_fallback_enabled = True
            mock_settings.health_check_interval_seconds = 60
            
            orchestrator = create_orchestrator(
                timeout_ms=3000,
                fallback_enabled=False,
            )
            assert orchestrator.timeout_ms == 3000
            assert orchestrator.fallback_enabled is False
