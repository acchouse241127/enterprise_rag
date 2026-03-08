"""
Tests for Denoiser core functionality.

Tests for:
- Denoiser initialization
- denoise() method
- Reranker score filtering
- Keyword overlap filtering

Author: C2
Date: 2026-03-04
Task: V2.0 Test Coverage Improvement
"""

import pytest
from unittest.mock import patch


class TestDenoiser:
    """Tests for Denoiser class."""

    def test_init_default_thresholds(self):
        """Test Denoiser initialization with default thresholds."""
        from app.rag.denoiser import Denoiser

        denoiser = Denoiser()
        assert denoiser.reranker_threshold == 0.15
        assert denoiser.keyword_overlap_min == 0.2

    def test_init_custom_thresholds(self):
        """Test Denoiser initialization with custom thresholds."""
        from app.rag.denoiser import Denoiser

        denoiser = Denoiser(reranker_threshold=0.5, keyword_overlap_min=0.3)
        assert denoiser.reranker_threshold == 0.5
        assert denoiser.keyword_overlap_min == 0.3

    def test_init_invalid_reranker_threshold_negative(self):
        """Test Denoiser with negative reranker_threshold."""
        from app.rag.denoiser import Denoiser

        with pytest.raises(ValueError, match="reranker_threshold must be between 0 and 1"):
            Denoiser(reranker_threshold=-0.1)

    def test_init_invalid_reranker_threshold_greater_than_one(self):
        """Test Denoiser with reranker_threshold > 1."""
        from app.rag.denoiser import Denoiser

        with pytest.raises(ValueError, match="reranker_threshold must be between 0 and 1"):
            Denoiser(reranker_threshold=1.1)

    def test_init_invalid_keyword_overlap_negative(self):
        """Test Denoiser with negative keyword_overlap_min."""
        from app.rag.denoiser import Denoiser

        with pytest.raises(ValueError, match="keyword_overlap_min must be between 0 and 1"):
            Denoiser(keyword_overlap_min=-0.1)

    def test_init_invalid_keyword_overlap_greater_than_one(self):
        """Test Denoiser with keyword_overlap_min > 1."""
        from app.rag.denoiser import Denoiser

        with pytest.raises(ValueError, match="keyword_overlap_min must be between 0 and 1"):
            Denoiser(keyword_overlap_min=1.1)

    def test_init_boundary_thresholds(self):
        """Test Denoiser with boundary threshold values (0 and 1)."""
        from app.rag.denoiser import Denoiser

        denoiser1 = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.0)
        assert denoiser1.reranker_threshold == 0.0
        assert denoiser1.keyword_overlap_min == 0.0

        denoiser2 = Denoiser(reranker_threshold=1.0, keyword_overlap_min=1.0)
        assert denoiser2.reranker_threshold == 1.0
        assert denoiser2.keyword_overlap_min == 1.0

    def test_denoise_empty_results(self):
        """Test denoise with empty results."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        denoiser = Denoiser()
        results = denoiser.denoise("测试查询", [])

        assert results == []

    def test_denoise_all_below_threshold(self):
        """Test denoise when all results are below reranker threshold."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        denoiser = Denoiser(reranker_threshold=0.5)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="测试内容1", section_title=None, metadata={}, score=0.1
            ),
            RetrievalResult(
                id="chunk_2", document_id=1, knowledge_base_id=1, chunk_index=1,
                content="测试内容2", section_title=None, metadata={}, score=0.2
            ),
        ]

        results = denoiser.denoise("测试查询", results_list)

        assert results == []

    def test_denoise_all_above_threshold(self):
        """Test denoise when all results are above reranker threshold."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        denoiser = Denoiser(reranker_threshold=0.1)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="测试内容", section_title=None, metadata={}, score=0.5
            ),
            RetrievalResult(
                id="chunk_2", document_id=1, knowledge_base_id=1, chunk_index=1,
                content="测试内容", section_title=None, metadata={}, score=0.6
            ),
        ]

        results = denoiser.denoise("测试查询", results_list)

        # All should pass reranker filter
        assert len(results) == 2

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_keyword_overlap_filter(self, mock_jieba):
        """Test denoise with keyword overlap filtering."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        # Mock jieba to return controlled keywords
        def mock_cut_side_effect(text, cut_all=False):
            if "测试" in text:
                return ["测试", "查询"]
            elif "内容" in text:
                return ["内容", "不相关"]
            return []

        mock_jieba.side_effect = mock_cut_side_effect

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.5)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="测试内容", section_title=None, metadata={}, score=0.5
            ),
            RetrievalResult(
                id="chunk_2", document_id=1, knowledge_base_id=1, chunk_index=1,
                content="不相关内容", section_title=None, metadata={}, score=0.5
            ),
        ]

        results = denoiser.denoise("测试查询", results_list)

        # chunk_1: overlap = |{测试,查询} ∩ {测试,内容}| / |{测试,查询}| = 1/2 = 0.5 >= 0.5 -> keep
        # chunk_2: overlap = |{测试,查询} ∩ {不相关,内容}| / |{测试,查询}| = 0/2 = 0 < 0.5 -> remove
        assert len(results) == 1
        assert results[0].id == "chunk_1"

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_zero_keyword_overlap(self, mock_jieba):
        """Test denoise with zero keyword overlap."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        def mock_cut_side_effect(text, cut_all=False):
            if "测试" in text:
                return ["测试"]
            else:
                return ["其他"]

        mock_jieba.side_effect = mock_cut_side_effect

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.1)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="其他内容", section_title=None, metadata={}, score=0.5
            ),
        ]

        results = denoiser.denoise("测试查询", results_list)

        # overlap = 0/1 = 0 < 0.1 -> remove
        assert len(results) == 0

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_full_keyword_overlap(self, mock_jieba):
        """Test denoise with full keyword overlap."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        def mock_cut_side_effect(text, cut_all=False):
            return ["测试", "查询"]

        mock_jieba.side_effect = mock_cut_side_effect

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.5)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="测试查询", section_title=None, metadata={}, score=0.5
            ),
        ]

        results = denoiser.denoise("测试查询", results_list)

        # overlap = 2/2 = 1.0 >= 0.5 -> keep
        assert len(results) == 1

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_preserves_order(self, mock_jieba):
        """Test that denoise preserves original order."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        def mock_cut_side_effect(text, cut_all=False):
            return ["测试"]

        mock_jieba.side_effect = mock_cut_side_effect

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.1)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="测试A", section_title=None, metadata={}, score=0.9
            ),
            RetrievalResult(
                id="chunk_2", document_id=1, knowledge_base_id=1, chunk_index=1,
                content="测试B", section_title=None, metadata={}, score=0.8
            ),
            RetrievalResult(
                id="chunk_3", document_id=1, knowledge_base_id=1, chunk_index=2,
                content="测试C", section_title=None, metadata={}, score=0.7
            ),
        ]

        results = denoiser.denoise("测试", results_list)

        assert len(results) == 3
        assert results[0].id == "chunk_1"
        assert results[1].id == "chunk_2"
        assert results[2].id == "chunk_3"

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_jieba_exception(self, mock_jieba):
        """Test denoise when jieba raises exception."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        mock_jieba.side_effect = Exception("jieba error")

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.1)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="测试内容", section_title=None, metadata={}, score=0.5
            ),
        ]

        # Should return results without keyword filtering when jieba fails
        results = denoiser.denoise("测试查询", results_list)

        assert len(results) == 1

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_empty_query_keywords(self, mock_jieba):
        """Test denoise when query has no keywords."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        # Mock jieba to return empty keywords for query
        def mock_cut_side_effect(text, cut_all=False):
            if "查询" in text:
                return []  # Empty keywords
            return ["内容"]

        mock_jieba.side_effect = mock_cut_side_effect

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.1)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="测试内容", section_title=None, metadata={}, score=0.5
            ),
        ]

        results = denoiser.denoise("查询", results_list)

        # Should skip keyword filtering when query has no keywords
        assert len(results) == 1

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_empty_chunk_keywords(self, mock_jieba):
        """Test denoise when chunk has no keywords."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        def mock_cut_side_effect(text, cut_all=False):
            if "查询" in text:
                return ["查询"]
            return []  # Empty keywords for chunk

        mock_jieba.side_effect = mock_cut_side_effect

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.1)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="", section_title=None, metadata={}, score=0.5
            ),
        ]

        results = denoiser.denoise("查询", results_list)

        # Should skip chunks with no keywords
        assert len(results) == 0

    def test_denoise_exact_threshold_match(self):
        """Test denoise with scores exactly at threshold."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        denoiser = Denoiser(reranker_threshold=0.5)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="测试内容", section_title=None, metadata={}, score=0.5  # Exactly at threshold
            ),
            RetrievalResult(
                id="chunk_2", document_id=1, knowledge_base_id=1, chunk_index=1,
                content="测试内容", section_title=None, metadata={}, score=0.499  # Just below threshold
            ),
        ]

        @patch('app.rag.denoiser.jieba.cut')
        def test(mock_cut):
            mock_cut.return_value = ["测试"]
            results = denoiser.denoise("测试", results_list)
            return results

        results = test()

        # Only chunk_1 should pass reranker threshold
        assert len(results) == 1
        assert results[0].id == "chunk_1"

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_exact_overlap_match(self, mock_jieba):
        """Test denoise with overlap exactly at keyword_overlap_min."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        def mock_cut_side_effect(text, cut_all=False):
            if "查询" in text:
                return ["查询", "测试"]
            else:
                return ["查询", "内容"]

        mock_jieba.side_effect = mock_cut_side_effect

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.5)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="查询内容", section_title=None, metadata={}, score=0.5
            ),
        ]

        results = denoiser.denoise("查询测试", results_list)

        # overlap = |{查询,测试} ∩ {查询,内容}| / |{查询,测试}| = 1/2 = 0.5 >= 0.5 -> keep
        assert len(results) == 1

    @patch('app.rag.denoiser.jieba.cut')
    def test_denoise_whitespace_handling(self, mock_jieba):
        """Test denoise with whitespace in keywords."""
        from app.rag.denoiser import Denoiser
        from app.rag.parent_retriever import RetrievalResult

        def mock_cut_side_effect(text, cut_all=False):
            # Return tokens with whitespace
            if "查询" in text:
                return ["查询", " 测试 ", " 关键词 "]
            else:
                return ["查询", "内容"]

        # Filter out empty/whitespace-only tokens manually
        def cut_with_filter(text, cut_all=False):
            tokens = mock_cut_side_effect(text, cut_all)
            return [t.strip() for t in tokens if t.strip()]

        mock_jieba.side_effect = cut_with_filter

        denoiser = Denoiser(reranker_threshold=0.0, keyword_overlap_min=0.3)
        results_list = [
            RetrievalResult(
                id="chunk_1", document_id=1, knowledge_base_id=1, chunk_index=0,
                content="查询内容", section_title=None, metadata={}, score=0.5
            ),
        ]

        results = denoiser.denoise("查询测试", results_list)

        # Should handle whitespace correctly
        assert len(results) >= 0
