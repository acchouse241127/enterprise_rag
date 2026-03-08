"""Comprehensive tests for HybridRetrievalPipeline module.

Tests cover:
- Pipeline initialization
- Complete retrieval workflow
- BM25 and vector retrieval
- RRF fusion
- Parent document retrieval
- Reranking
- Adaptive top-k selection
- Denoising
- Latency measurement
- Various configuration options
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.rag.parent_retriever import RetrievalResult
from app.rag.hybrid_pipeline import HybridRetrievalPipeline


class TestHybridRetrievalPipelineInit:
    """Tests for HybridRetrievalPipeline initialization."""

    def test_pipeline_init(self):
        """Test pipeline initialization with all components."""
        mock_bm25 = MagicMock()
        mock_vector = MagicMock()
        mock_rrf = MagicMock()
        mock_parent = MagicMock()
        mock_adaptive = MagicMock()
        mock_denoiser = MagicMock()
        mock_reranker = MagicMock()

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        assert pipeline.bm25_retriever is mock_bm25
        assert pipeline.vector_retriever is mock_vector
        assert pipeline.rrf_fusion is mock_rrf
        assert pipeline.parent_retriever is mock_parent
        assert pipeline.adaptive_topk is mock_adaptive
        assert pipeline.denoiser is mock_denoiser
        assert pipeline.reranker is mock_reranker


class TestHybridRetrievalPipelineRetrieve:
    """Tests for HybridRetrievalPipeline.retrieve method."""

    def _create_bm25_results(self, count):
        """Helper to create BM25Result-like objects."""
        from app.rag.bm25_retriever import BM25Result
        results = []
        for i in range(count):
            result = MagicMock()
            result.id = f"bm25_{i}"
            result.document_id = i
            result.knowledge_base_id = 1
            result.chunk_index = i
            result.content = f"bm25_content_{i}"
            result.section_title = f"bm25_title_{i}"
            result.metadata = {"source": "bm25"}
            result.bm25_score = 0.9 - (i * 0.1)
            results.append(result)
        return results

    def _create_vector_results(self, count):
        """Helper to create vector retrieval results."""
        results = []
        for i in range(count):
            results.append({
                "id": f"vector_{i}",
                "document_id": i + count,
                "knowledge_base_id": 1,
                "chunk_index": i + count,
                "content": f"vector_content_{i}",
                "section_title": f"vector_title_{i}",
                "metadata": {"source": "vector"},
            })
        # vector_retriever.retrieve returns (results, metadata)
        return results, {"vector_latency_ms": 10}

    @pytest.mark.asyncio
    async def test_retrieve_basic_flow(self):
        """Test basic retrieval flow with default parameters."""
        # Setup mocks
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(10), {}))

        mock_vector = MagicMock()
        # vector_retriever.retrieve returns (results, metadata)
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(10))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(10)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"fused_content_{i}"
            r.section_title = f"fused_title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.05)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:10])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.95 - (i * 0.05)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()
        mock_adaptive.select = MagicMock(return_value=rrf_results[:5])

        mock_denoiser = MagicMock()
        mock_denoiser.denoise = MagicMock(return_value=rrf_results[:5])

        # Create pipeline
        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        # Execute
        results, latency = await pipeline.retrieve(
            query="test query",
            knowledge_base_id=1,
            top_k=5,
        )

        # Verify
        assert len(results) == 5
        assert "bm25_ms" in latency
        assert "vector_ms" in latency
        assert "rrf_ms" in latency
        assert "parent_expand_ms" in latency
        assert "reranker_ms" in latency
        assert "adaptive_topk_ms" in latency
        assert "denoise_ms" in latency

    @pytest.mark.asyncio
    async def test_retrieve_custom_top_k(self):
        """Test retrieval with custom top_k parameter."""
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(20), {}))

        mock_vector = MagicMock()
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(20))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(20)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"content_{i}"
            r.section_title = f"title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.02)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:20])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.95 - (i * 0.02)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()
        mock_adaptive.select = MagicMock(return_value=rrf_results[:10])

        mock_denoiser = MagicMock()
        mock_denoiser.denoise = MagicMock(return_value=rrf_results[:10])

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=10,
        )

        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_retrieve_parent_mode_physical(self):
        """Test retrieval with physical parent mode."""
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(10), {}))

        mock_vector = MagicMock()
        # vector_retriever.retrieve returns (results, metadata)
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(10))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(10)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"content_{i}"
            r.section_title = f"title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.05)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:10])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.9 - (i * 0.05)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()
        mock_adaptive.select = MagicMock(return_value=rrf_results[:5])

        mock_denoiser = MagicMock()
        mock_denoiser.denoise = MagicMock(return_value=rrf_results[:5])

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            parent_retrieval_mode="physical",
        )

        mock_parent.retrieve.assert_called_once()
        call_args = mock_parent.retrieve.call_args
        # Check mode parameter in kwargs
        assert call_args[1].get("mode") == "physical"

    @pytest.mark.asyncio
    async def test_retrieve_parent_mode_off(self):
        """Test retrieval with parent mode off."""
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(10), {}))

        mock_vector = MagicMock()
        # vector_retriever.retrieve returns (results, metadata)
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(10))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(10)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"content_{i}"
            r.section_title = f"title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.05)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:10])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.9 - (i * 0.05)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()
        mock_adaptive.select = MagicMock(return_value=rrf_results[:5])

        mock_denoiser = MagicMock()
        mock_denoiser.denoise = MagicMock(return_value=rrf_results[:5])

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            parent_retrieval_mode="off",
        )

        call_args = mock_parent.retrieve.call_args
        # Check mode parameter in kwargs
        assert call_args[1].get("mode") == "off"  # mode parameter

    @pytest.mark.asyncio
    async def test_retrieve_dynamic_expand_n(self):
        """Test retrieval with dynamic expand_n parameter."""
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(10), {}))

        mock_vector = MagicMock()
        # vector_retriever.retrieve returns (results, metadata)
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(10))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(10)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"content_{i}"
            r.section_title = f"title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.05)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:10])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.9 - (i * 0.05)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()
        mock_adaptive.select = MagicMock(return_value=rrf_results[:5])

        mock_denoiser = MagicMock()
        mock_denoiser.denoise = MagicMock(return_value=rrf_results[:5])

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            parent_retrieval_mode="dynamic",
            dynamic_expand_n=3,
        )

        call_args = mock_parent.retrieve.call_args
        assert call_args[1]["dynamic_expand_n"] == 3

    @pytest.mark.asyncio
    async def test_retrieve_disable_adaptive(self):
        """Test retrieval with adaptive top-k disabled."""
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(10), {}))

        mock_vector = MagicMock()
        # vector_retriever.retrieve returns (results, metadata)
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(10))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(10)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"content_{i}"
            r.section_title = f"title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.05)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:10])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.9 - (i * 0.05)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()

        mock_denoiser = MagicMock()
        mock_denoiser.denoise = MagicMock(return_value=rrf_results[:5])

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            enable_adaptive=False,
        )

        # adaptive.select should not be called
        mock_adaptive.select.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieve_disable_denoise(self):
        """Test retrieval with denoising disabled."""
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(10), {}))

        mock_vector = MagicMock()
        # vector_retriever.retrieve returns (results, metadata)
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(10))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(10)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"content_{i}"
            r.section_title = f"title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.05)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:10])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.9 - (i * 0.05)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()
        mock_adaptive.select = MagicMock(return_value=rrf_results[:5])

        mock_denoiser = MagicMock()

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            enable_denoise=False,
        )

        # denoiser.denoise should not be called
        mock_denoiser.denoise.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieve_latency_measurement(self):
        """Test that latency is measured for each stage."""
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(10), {}))

        mock_vector = MagicMock()
        # vector_retriever.retrieve returns (results, metadata)
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(10))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(10)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"content_{i}"
            r.section_title = f"title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.05)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:10])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.9 - (i * 0.05)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()
        mock_adaptive.select = MagicMock(return_value=rrf_results[:5])

        mock_denoiser = MagicMock()
        mock_denoiser.denoise = MagicMock(return_value=rrf_results[:5])

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        results, latency = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
        )

        # Check all latency keys exist
        expected_keys = [
            "bm25_ms",
            "vector_ms",
            "rrf_ms",
            "parent_expand_ms",
            "reranker_ms",
            "adaptive_topk_ms",
            "denoise_ms",
        ]
        for key in expected_keys:
            assert key in latency
            assert isinstance(latency[key], int)
            assert latency[key] >= 0

    @pytest.mark.asyncio
    async def test_retrieve_results_truncated_to_top_k(self):
        """Test that final results are truncated to requested top_k."""
        mock_bm25 = MagicMock()
        mock_bm25.search = MagicMock(return_value=(self._create_bm25_results(20), {}))

        mock_vector = MagicMock()
        mock_vector.retrieve = MagicMock(return_value=self._create_vector_results(20))

        mock_rrf = MagicMock()
        rrf_results = [MagicMock() for _ in range(20)]
        for i, r in enumerate(rrf_results):
            r.id = f"fused_{i}"
            r.document_id = i
            r.knowledge_base_id = 1
            r.chunk_index = i
            r.content = f"content_{i}"
            r.section_title = f"title_{i}"
            r.metadata = {}
            r.rrf_score = 0.9 - (i * 0.02)
        mock_rrf.fuse = MagicMock(return_value=rrf_results)

        mock_parent = MagicMock()
        mock_parent.retrieve = AsyncMock(return_value=rrf_results[:20])

        mock_reranker = MagicMock()
        reranked = [{"id": r.id, "content": r.content, "rerank_score": 0.9 - (i * 0.02)}
                    for i, r in enumerate(rrf_results)]
        mock_reranker.rerank = MagicMock(return_value=reranked)

        mock_adaptive = MagicMock()
        mock_adaptive.select = MagicMock(return_value=rrf_results[:10])

        mock_denoiser = MagicMock()
        mock_denoiser.denoise = MagicMock(return_value=rrf_results[:10])

        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker,
        )

        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=3,
        )

        # Should be truncated to top_k
        assert len(results) == 3
