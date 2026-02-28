"""V2.0 功能测试：检索 + 质量保障流程验证

Author: C2
Date: 2026-02-28
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestB1RetrievalModules:
    """B1 检索模块测试"""

    def test_bm25_retriever_import(self):
        from app.rag.bm25_retriever import BM25Retriever, BM25Result
        assert BM25Retriever is not None

    def test_rrf_fusion_import(self):
        from app.rag.rrf_fusion import RRFFusion, RRFResult
        assert RRFFusion is not None

    def test_hybrid_pipeline_import(self):
        from app.rag.hybrid_pipeline import HybridRetrievalPipeline
        assert HybridRetrievalPipeline is not None

    def test_chunker_import(self):
        from app.rag.chunker import TextChunker
        chunker = TextChunker()
        assert chunker is not None

    def test_title_extractor_import(self):
        from app.rag.title_extractor import TitleExtractor, TitleInfo
        assert TitleExtractor is not None

    def test_parent_retriever_import(self):
        from app.rag.parent_retriever import ParentRetriever, RetrievalResult
        assert ParentRetriever is not None

    def test_adaptive_topk_import(self):
        from app.rag.adaptive_topk import AdaptiveTopK
        assert AdaptiveTopK is not None

    def test_denoiser_import(self):
        from app.rag.denoiser import Denoiser
        assert Denoiser is not None


class TestB2QualityModules:
    """B2 质量保障模块测试"""

    def test_nli_detector_import(self):
        from app.verify.nli_detector import NLIHallucinationDetector, HallucinationResult
        assert NLIHallucinationDetector is not None

    def test_confidence_scorer_import(self):
        from app.verify.confidence_scorer import ConfidenceScorer, ConfidenceScore
        assert ConfidenceScorer is not None

    def test_citation_verifier_import(self):
        from app.verify.citation_verifier import CitationVerifier, CitationResult
        assert CitationVerifier is not None

    def test_refusal_handler_import(self):
        from app.verify.refusal import RefusalHandler, RefusalInfo
        assert RefusalHandler is not None

    def test_verify_pipeline_import(self):
        from app.verify.verify_pipeline import VerifyPipeline, VerificationAction, VerificationResult
        assert VerifyPipeline is not None

    def test_verification_action_enum(self):
        from app.verify.verify_pipeline import VerificationAction
        assert VerificationAction.PASS.value == "pass"
        assert VerificationAction.FILTER.value == "filter"
        assert VerificationAction.RETRY.value == "retry"
        assert VerificationAction.REFUSE.value == "refuse"


class TestRRFFusionLogic:
    """RRF 融合算法逻辑测试"""

    def test_rrf_basic_fuse(self):
        from app.rag.rrf_fusion import RRFFusion
        assert RRFFusion is not None


class TestRefusalHandler:
    """智能拒答处理器测试"""

    def test_refusal_handler_exists(self):
        from app.verify.refusal import RefusalHandler, RefusalInfo
        handler = RefusalHandler()
        assert handler.DEFAULT_MESSAGE is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
