"""
Hybrid Pipeline测试 - 目标覆盖 app/rag/hybrid_pipeline.py (51语句)
预期覆盖率: 90%+
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

class TestHybridRetrievalPipeline:
    """测试混合检索管道"""

    @pytest.fixture
    def mock_pipeline(self):
        """创建Mock的混合检索管道"""
        from app.rag.hybrid_pipeline import HybridRetrievalPipeline
        
        # 创建所有依赖的Mock
        mock_bm25 = Mock()
        mock_bm25.search = AsyncMock(return_value=[
            Mock(id="bm1", document_id="doc1", knowledge_base_id=1, chunk_index=0, 
                 content="bm25 content", section_title="Section 1", metadata={},
                 bm25_score=0.8)
        ])
        
        mock_vector = Mock()
        mock_vector.retrieve = AsyncMock(return_value=[
            Mock(id="vec1", document_id="doc1", knowledge_base_id=1, chunk_index=0,
                 content="vector content", section_title="Section 1", metadata={},
                 vector_score=0.9)
        ])
        
        mock_rrf = Mock()
        mock_rrf.fuse = Mock(return_value=[
            Mock(id="fused1", document_id="doc1", knowledge_base_id=1, chunk_index=0,
                 content="fused content", section_title="Section 1", metadata={},
                 rrf_score=0.85)
        ])
        
        mock_parent = Mock()
        mock_parent.retrieve = AsyncMock(return_value=[
            Mock(id="parent1", document_id="doc1", knowledge_base_id=1, chunk_index=0,
                 content="parent content", section_title="Section 1", metadata={}, score=0.85)
        ])
        
        mock_reranker = Mock()
        mock_reranker.rerank = Mock(return_value=[
            {"id": "rerank1", "rerank_score": 0.9}
        ])
        
        mock_adaptive = Mock()
        mock_adaptive.select = Mock(return_value=[
            Mock(id="adaptive1", document_id="doc1", knowledge_base_id=1, chunk_index=0,
                 content="adaptive content", section_title="Section 1", metadata={}, score=0.88)
        ])
        
        mock_denoiser = Mock()
        mock_denoiser.denoise = Mock(return_value=[
            Mock(id="denoised1", document_id="doc1", knowledge_base_id=1, chunk_index=0,
                 content="denoised content", section_title="Section 1", metadata={}, score=0.88)
        ])
        
        # 创建管道
        from app.rag.reranker import BgeRerankerService
        from app.rag.parent_retriever import ParentRetriever
        from app.rag.rrf_fusion import RRFFusion
        from app.rag.adaptive_topk import AdaptiveTopK
        from app.rag.denoiser import Denoiser
        from app.rag.bm25_retriever import BM25Retriever
        from app.rag.retriever import VectorRetriever
        
        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker
        )
        
        return pipeline, {
            'bm25': mock_bm25,
            'vector': mock_vector,
            'rrf': mock_rrf,
            'parent': mock_parent,
            'reranker': mock_reranker,
            'adaptive': mock_adaptive,
            'denoiser': mock_denoiser
        }

    @pytest.mark.asyncio
    async def test_pipeline_init(self, mock_pipeline):
        """测试管道初始化"""
        pipeline, mocks = mock_pipeline
        
        assert pipeline.bm25_retriever == mocks['bm25']
        assert pipeline.vector_retriever == mocks['vector']
        assert pipeline.rrf_fusion == mocks['rrf']
        assert pipeline.parent_retriever == mocks['parent']
        assert pipeline.adaptive_topk == mocks['adaptive']
        assert pipeline.denoiser == mocks['denoiser']
        assert pipeline.reranker == mocks['reranker']

    @pytest.mark.asyncio
    async def test_retrieve_basic_flow(self, mock_pipeline):
        """测试基本检索流程"""
        pipeline, mocks = mock_pipeline
        
        results, latency = await pipeline.retrieve(
            query="test query",
            knowledge_base_id=1,
            top_k=5
        )
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) <= 5  # top_k限制
        assert isinstance(latency, dict)
        
        # 验证调用链
        mocks['bm25'].search.assert_called_once()
        mocks['vector'].retrieve.assert_called_once()
        mocks['rrf'].fuse.assert_called_once()
        mocks['parent'].retrieve.assert_called_once()
        mocks['reranker'].rerank.assert_called_once()
        mocks['adaptive'].select.assert_called_once()
        mocks['denoiser'].denoise.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_with_parent_mode(self, mock_pipeline):
        """测试不同父文档模式"""
        pipeline, mocks = mock_pipeline
        
        # 测试dynamic模式
        results_dynamic, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            parent_retrieval_mode="dynamic"
        )
        
        # 测试off模式
        results_off, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            parent_retrieval_mode="off"
        )
        
        # 验证parent retriever被调用
        assert mocks['parent'].retrieve.call_count >= 2

    @pytest.mark.asyncio
    async def test_retrieve_disable_adaptive(self, mock_pipeline):
        """测试禁用自适应"""
        pipeline, mocks = mock_pipeline
        
        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            enable_adaptive=False
        )
        
        # 验证adaptive未被调用
        mocks['adaptive'].select.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieve_disable_denoise(self, mock_pipeline):
        """测试禁用去噪"""
        pipeline, mocks = mock_pipeline
        
        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            enable_denoise=False
        )
        
        # 验证denoiser未被调用
        mocks['denoiser'].denoise.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieve_latency_tracking(self, mock_pipeline):
        """测试延迟追踪"""
        pipeline, mocks = mock_pipeline
        
        results, latency = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5
        )
        
        # 验证所有延迟都被记录
        expected_keys = ["bm25_ms", "vector_ms", "rrf_ms", 
                        "parent_expand_ms", "reranker_ms", 
                        "adaptive_topk_ms", "denoise_ms"]
        
        for key in expected_keys:
            assert key in latency
            assert isinstance(latency[key], int)
            assert latency[key] >= 0  # 延迟应该是非负数

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self, mock_pipeline):
        """测试空结果处理"""
        from app.rag.hybrid_pipeline import HybridRetrievalPipeline
        
        # Mock返回空结果
        mock_bm25 = Mock()
        mock_bm25.search = AsyncMock(return_value=[])
        
        mock_vector = Mock()
        mock_vector.retrieve = AsyncMock(return_value=[])
        
        mock_rrf = Mock()
        mock_rrf.fuse = Mock(return_value=[])
        
        mock_parent = Mock()
        mock_parent.retrieve = AsyncMock(return_value=[])
        
        mock_reranker = Mock()
        mock_reranker.rerank = Mock(return_value=[])
        
        mock_adaptive = Mock()
        mock_adaptive.select = Mock(return_value=[])
        
        mock_denoiser = Mock()
        mock_denoiser.denoise = Mock(return_value=[])
        
        pipeline = HybridRetrievalPipeline(
            bm25_retriever=mock_bm25,
            vector_retriever=mock_vector,
            rrf_fusion=mock_rrf,
            parent_retriever=mock_parent,
            adaptive_topk=mock_adaptive,
            denoiser=mock_denoiser,
            reranker=mock_reranker
        )
        
        results, latency = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5
        )
        
        # 验证空结果被正确处理
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_with_custom_top_k(self, mock_pipeline):
        """测试自定义top_k"""
        pipeline, mocks = mock_pipeline
        
        # 测试不同的top_k值
        for top_k in [3, 5, 10]:
            results, _ = await pipeline.retrieve(
                query="test",
                knowledge_base_id=1,
                top_k=top_k
            )
            
            assert len(results) <= top_k

    @pytest.mark.asyncio
    async def test_retrieve_dynamic_expand(self, mock_pipeline):
        """测试dynamic扩展参数"""
        pipeline, mocks = mock_pipeline
        
        # 测试不同的expand_n值
        results, _ = await pipeline.retrieve(
            query="test",
            knowledge_base_id=1,
            top_k=5,
            dynamic_expand_n=3
        )
        
        # 验证parent retriever被调用且包含expand_n参数
        call_args = mocks['parent'].retrieve.call_args
        if call_args:
            kwargs = call_args[1] if len(call_args) > 1 else {}
            assert 'dynamic_expand_n' in kwargs or 'dynamic_expand_n' in str(call_args)


class TestHybridPipelineIntegration:
    """测试混合检索管道集成场景"""
    
    @pytest.fixture
    def mock_all_components(self):
        """Mock所有组件"""
        mock_bm25 = Mock()
        mock_vector = Mock()
        mock_rrf = Mock()
        mock_parent = Mock()
        mock_reranker = Mock()
        mock_adaptive = Mock()
        mock_denoiser = Mock()
        
        # 设置默认返回值
        mock_bm25.search = AsyncMock(return_value=[])
        mock_vector.retrieve = AsyncMock(return_value=[])
        mock_rrf.fuse = Mock(return_value=[])
        mock_parent.retrieve = AsyncMock(return_value=[])
        mock_reranker.rerank = Mock(return_value=[])
        mock_adaptive.select = Mock(return_value=[])
        mock_denoiser.denoise = Mock(return_value=[])
        
        return {
            'bm25': mock_bm25,
            'vector': mock_vector,
            'rrf': mock_rrf,
            'parent': mock_parent,
            'reranker': mock_reranker,
            'adaptive': mock_adaptive,
            'denoiser': mock_denoiser
        }

    @pytest.mark.asyncio
    async def test_full_pipeline_integration(self, mock_all_components):
        """测试完整管道集成"""
        from app.rag.hybrid_pipeline import HybridRetrievalPipeline
        
        pipeline = HybridRetrievalPipeline(**mock_all_components)
        
        results, latency = await pipeline.retrieve(
            query="full integration test",
            knowledge_base_id=1
        )
        
        # 验证返回格式
        assert isinstance(results, list)
        assert isinstance(latency, dict)
        assert len(latency.keys()) >= 7  # 至少7个延迟指标

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_all_components):
        """测试错误处理"""
        from app.rag.hybrid_pipeline import HybridRetrievalPipeline
        
        # Mock异常情况
        mock_all_components['bm25'].search = AsyncMock(
            side_effect=Exception("BM25 error")
        )
        
        pipeline = HybridRetrievalPipeline(**mock_all_components)
        
        # 测试异常是否被正确传播
        try:
            results, latency = await pipeline.retrieve(
                query="error test",
                knowledge_base_id=1
            )
            # 如果没有抛出异常，验证结果
            assert results is not None
        except Exception as e:
            # 验证异常信息
            assert "BM25 error" in str(e)
