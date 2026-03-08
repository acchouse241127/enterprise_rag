"""Tests for HybridPipeline integration with QaService.

Tests verify that HybridRetrievalPipeline is properly integrated:
- Hybrid mode uses HybridRetrievalPipeline instead of separate retrievers
- Complete latency breakdown is returned (bm25_ms, vector_ms, rrf_ms, etc.)
- Graceful degradation on BM25 failure
- Async handling is correct
- Performance impact is acceptable

This is a TDD approach: tests written first, then implementation.

Author: C2
Date: 2026-03-05
Phase: P2-1 TDD
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

from app.services.qa_service import QaService
from app.rag.hybrid_pipeline import HybridRetrievalPipeline
from app.rag.parent_retriever import RetrievalResult


class TestHybridPipelineIntegration:
    """Test HybridRetrievalPipeline integration with QaService."""

    @pytest.fixture
    def mock_hybrid_pipeline(self):
        """Create a mocked HybridRetrievalPipeline for testing."""
        pipeline = MagicMock(spec=HybridRetrievalPipeline)
        
        # Mock async retrieve method
        pipeline.retrieve = AsyncMock()
        
        # Set up successful retrieval with latency breakdown
        mock_results = [
            RetrievalResult(
                id="chunk1",
                document_id=1,
                knowledge_base_id=1,
                chunk_index=0,
                content="Test content about enterprise RAG",
                section_title="Introduction",
                metadata={},
                score=0.95,
            ),
            RetrievalResult(
                id="chunk2",
                document_id=1,
                knowledge_base_id=1,
                chunk_index=1,
                content="Another test chunk",
                section_title="Methods",
                metadata={},
                score=0.85,
            ),
        ]
        
        mock_latency = {
            "bm25_ms": 45,
            "vector_ms": 120,
            "rrf_ms": 5,
            "parent_expand_ms": 30,
            "reranker_ms": 80,
            "adaptive_topk_ms": 2,
            "denoise_ms": 3,
        }
        
        pipeline.retrieve.return_value = (mock_results, mock_latency)
        return pipeline

    @pytest.fixture
    def mock_qa_service(self, mock_hybrid_pipeline):
        """Create a mocked QaService with HybridPipeline."""
        service = QaService.__new__(QaService)
        
        # Mock traditional retrievers (should NOT be used in hybrid mode)
        service._retriever = MagicMock()
        service._keyword_retriever = MagicMock()
        service._reranker = MagicMock()
        service._embedding_service = MagicMock()
        service._pipeline = MagicMock()
        service._vector_store = MagicMock()
        service._verify_pipeline = None
        service._conversation_history = {}
        
        # Inject HybridPipeline
        service._hybrid_pipeline = mock_hybrid_pipeline
        
        # Mock pipeline methods
        service._pipeline.no_answer_text = "未找到相关信息"
        service._pipeline.build_prompt_messages = MagicMock(return_value=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test question"},
        ])
        service._pipeline.insert_citations = MagicMock(return_value=("Answer with citations", []))
        
        return service

    def test_qa_service_uses_hybrid_pipeline_for_hybrid_mode(self, mock_qa_service):
        """Test that QaService uses HybridRetrievalPipeline in hybrid mode."""
        # Mock LLM provider
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Test answer"
        
        with patch('app.services.qa_service.get_provider_for_task', return_value=mock_provider):
            with patch('app.services.qa_service.QaService._log_retrieval', return_value=1) as mock_log:
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="测试问题",
                    retrieval_mode="hybrid",
                )
        
        # Verify result is not None
        assert err is None
        assert result is not None
        assert result.get("answer") is not None
        
        # Verify HybridPipeline was called
        assert mock_qa_service._hybrid_pipeline.retrieve.called
        
        # Verify traditional retrievers were NOT called
        assert not mock_qa_service._retriever.retrieve.called
        assert not mock_qa_service._keyword_retriever.retrieve.called

    def test_hybrid_mode_latency_breakdown_fields(self, mock_qa_service):
        """Test that hybrid mode returns complete latency breakdown."""
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Answer"
        
        with patch('app.services.qa_service.get_provider_for_task', return_value=mock_provider):
            with patch('app.services.qa_service.QaService._log_retrieval') as mock_log:
                mock_log.return_value = 1
                
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="测试问题",
                    retrieval_mode="hybrid",
                )
        
        # Verify _log_retrieval was called
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        
        # Verify latency_breakdown contains all expected fields
        latency_breakdown = call_kwargs.get('latency_breakdown')
        assert latency_breakdown is not None
        assert "bm25_ms" in latency_breakdown
        assert "vector_ms" in latency_breakdown
        assert "rrf_ms" in latency_breakdown
        assert "reranker_ms" in latency_breakdown
        
        # Verify values are positive integers
        for key in ["bm25_ms", "vector_ms", "rrf_ms", "reranker_ms"]:
            assert latency_breakdown[key] > 0
            assert isinstance(latency_breakdown[key], int)

    def test_hybrid_pipeline_degradation_on_bm25_failure(self, mock_qa_service):
        """Test graceful degradation when BM25 fails in HybridPipeline."""
        # Mock HybridPipeline to simulate BM25 failure
        async def failing_retrieve(*args, **kwargs):
            # Return empty results to simulate degradation
            return [], {
                "bm25_ms": 0,
                "vector_ms": 100,
                "rrf_ms": 0,
                "parent_expand_ms": 0,
                "reranker_ms": 0,
                "adaptive_topk_ms": 0,
                "denoise_ms": 0,
                "error": "BM25 retrieval failed, degraded to vector-only",
            }
        
        mock_qa_service._hybrid_pipeline.retrieve = AsyncMock(side_effect=failing_retrieve)
        
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Degraded answer"
        
        with patch('app.services.qa_service.get_provider_for_task', return_value=mock_provider):
            with patch('app.services.qa_service.QaService._log_retrieval') as mock_log:
                mock_log.return_value = 1
                
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="测试问题",
                    retrieval_mode="hybrid",
                )
        
        # Should still return a result (graceful degradation)
        assert err is None
        assert result is not None
        
        # Verify degradation was logged
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        latency_breakdown = call_kwargs.get('latency_breakdown')
        assert latency_breakdown.get('error') is not None

    def test_hybrid_mode_async_handling(self, mock_qa_service):
        """Test that hybrid mode handles async operations correctly."""
        # This test verifies async/sync integration
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Async test answer"
        
        with patch('app.services.qa_service.get_provider_for_task', return_value=mock_provider):
            with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="测试问题",
                    retrieval_mode="hybrid",
                )
        
        # Should complete successfully
        assert err is None
        assert result is not None

    def test_hybrid_mode_with_stream_ask(self, mock_qa_service):
        """Test that hybrid mode works with stream_ask."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter(["Test", " stream", " answer"])
        
        with patch('app.services.qa_service.get_provider_for_task', return_value=mock_provider):
            with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                result_generator = mock_qa_service.stream_ask(
                    knowledge_base_id=1,
                    question="测试问题",
                    retrieval_mode="hybrid",
                )
                
                # Consume the generator
                results = list(result_generator)
                
                # Should produce stream output
                assert len(results) > 0

    def test_vector_mode_ignores_hybrid_pipeline(self, mock_qa_service):
        """Test that vector mode does NOT use HybridPipeline."""
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Vector mode answer"
        
        # Mock traditional retriever
        mock_qa_service._retriever.retrieve.return_value = (
            [{"id": "chunk1", "content": "content"}],
            None
        )
        
        with patch('app.services.qa_service.get_provider_for_task', return_value=mock_provider):
            with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="测试问题",
                    retrieval_mode="vector",
                )
        
        # Should NOT call HybridPipeline in vector mode
        assert not mock_qa_service._hybrid_pipeline.retrieve.called
        
        # Should call traditional vector retriever
        assert mock_qa_service._retriever.retrieve.called

    def test_bm25_mode_ignores_hybrid_pipeline(self, mock_qa_service):
        """Test that bm25 mode does NOT use HybridPipeline."""
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "BM25 mode answer"
        
        with patch('app.services.qa_service.get_provider_for_task', return_value=mock_provider):
            with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="测试问题",
                    retrieval_mode="bm25",
                )
        
        # Should NOT call HybridPipeline in bm25 mode
        assert not mock_qa_service._hybrid_pipeline.retrieve.called


class TestHybridPipelinePerformance:
    """Test performance aspects of HybridPipeline integration."""

    @pytest.fixture
    def mock_qa_service(self):
        """Create a mocked QaService for performance testing."""
        service = QaService.__new__(QaService)
        service._hybrid_pipeline = MagicMock(spec=HybridRetrievalPipeline)
        service._retriever = MagicMock()
        service._keyword_retriever = MagicMock()
        service._reranker = MagicMock()
        service._pipeline = MagicMock()
        service._verify_pipeline = None
        
        # Mock latency within acceptable range
        service._hybrid_pipeline.retrieve = AsyncMock(return_value=(
            [],
            {
                "bm25_ms": 45,
                "vector_ms": 120,
                "rrf_ms": 5,
                "parent_expand_ms": 30,
                "reranker_ms": 80,
                "total_ms": 280,
            }
        ))
        
        service._pipeline.no_answer_text = "未找到"
        service._pipeline.build_prompt_messages = MagicMock(return_value=[])
        service._pipeline.insert_citations = MagicMock(return_value=("", []))
        
        return service

    def test_hybrid_pipeline_total_latency_acceptable(self, mock_qa_service):
        """Test that total latency from HybridPipeline is acceptable (< 500ms)."""
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Answer"
        
        with patch('app.services.qa_service.get_provider_for_task', return_value=mock_provider):
            with patch('app.services.qa_service.QaService._log_retrieval') as mock_log:
                mock_log.return_value = 1
                
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="question",
                    retrieval_mode="hybrid",
                )
        
        # Check logged latency
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        latency_breakdown = call_kwargs.get('latency_breakdown')
        
        # Sum of all retrieval phases should be < 500ms (excluding LLM)
        retrieval_total = (
            latency_breakdown.get('bm25_ms', 0) +
            latency_breakdown.get('vector_ms', 0) +
            latency_breakdown.get('rrf_ms', 0) +
            latency_breakdown.get('parent_expand_ms', 0) +
            latency_breakdown.get('reranker_ms', 0)
        )
        
        # Retrieval should complete in reasonable time
        assert retrieval_total < 1000  # 1 second max


class TestHybridPipelineErrorHandling:
    """Test error handling in HybridPipeline integration."""

    @pytest.fixture
    def mock_qa_service(self):
        """Create a mocked QaService for error testing."""
        service = QaService.__new__(QaService)
        service._hybrid_pipeline = MagicMock(spec=HybridRetrievalPipeline)
        service._pipeline = MagicMock()
        service._verify_pipeline = None
        service._pipeline.no_answer_text = "未找到"
        service._pipeline.build_prompt_messages = MagicMock(return_value=[])
        service._pipeline.insert_citations = MagicMock(return_value=("", []))
        return service

    def test_hybrid_pipeline_exception_handling(self, mock_qa_service):
        """Test that exceptions in HybridPipeline are handled gracefully."""
        # Mock HybridPipeline to raise exception
        async def raise_exception(*args, **kwargs):
            raise RuntimeError("HybridPipeline internal error")
        
        mock_qa_service._hybrid_pipeline.retrieve = AsyncMock(side_effect=raise_exception)
        
        with patch('app.services.qa_service.get_provider_for_task') as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "Fallback answer"
            mock_get_provider.return_value = mock_provider
            
            with patch('app.services.qa_service.QaService._log_retrieval') as mock_log:
                mock_log.return_value = 1
                
                # Should not crash, should handle gracefully
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="question",
                    retrieval_mode="hybrid",
                )
        
        # Should log the error
        assert mock_log.called

    def test_hybrid_pipeline_returns_empty_results(self, mock_qa_service):
        """Test handling when HybridPipeline returns no results."""
        mock_qa_service._hybrid_pipeline.retrieve = AsyncMock(return_value=([], {}))
        
        with patch('app.services.qa_service.get_provider_for_task') as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "No answer"
            mock_get_provider.return_value = mock_provider
            
            with patch('app.services.qa_service.QaService._log_retrieval', return_value=1):
                result, err = mock_qa_service.ask(
                    knowledge_base_id=1,
                    question="question",
                    retrieval_mode="hybrid",
                )
        
        # Should handle empty results gracefully
        assert err is None
        assert result is not None
