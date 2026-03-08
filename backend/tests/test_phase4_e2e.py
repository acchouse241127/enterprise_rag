"""End-to-end integration tests for V2.1 Phase 4.

Tests the complete multimodal retrieval enhancement pipeline
including query analysis, modality-aware ranking, and VLM enhancement.

Author: C2
Date: 2026-03-07
"""

import pytest

from app.rag.query_analyzer import QueryAnalyzer
from app.rag.modality_aware_retrieval import ModalityAwareRetrieval


class TestPhase4E2E:
    """End-to-end integration tests for Phase 4."""

    @pytest.fixture
    def query_analyzer(self):
        """Create query analyzer instance."""
        return QueryAnalyzer()

    @pytest.fixture
    def modality_retrieval(self):
        """Create modality-aware retrieval instance."""
        return ModalityAwareRetrieval()

    def test_query_chart_detection(self, query_analyzer):
        """Test chart query detection."""
        query = "显示销售趋势图表"
        result = query_analyzer.analyze(query)

        assert result["needs_chart"] is True
        assert result["needs_table"] is False
        assert result["needs_image"] is False
        assert result["chart_confidence"] > 0.5

    def test_query_table_detection(self, query_analyzer):
        """Test table query detection."""
        query = "查看数据表中的明细"
        result = query_analyzer.analyze(query)

        assert result["needs_chart"] is False
        assert result["needs_table"] is True
        assert result["needs_image"] is False
        assert result["table_confidence"] > 0.5

    def test_query_image_detection(self, query_analyzer):
        """Test image query detection."""
        query = "这张图片展示了什么"
        result = query_analyzer.analyze(query)

        assert result["needs_chart"] is False
        assert result["needs_table"] is False
        assert result["needs_image"] is True
        assert result["image_confidence"] > 0.5

    def test_query_classification(self, query_analyzer):
        """Test query type classification."""
        assert query_analyzer.classify_query_type("显示图表") == "chart"
        assert query_analyzer.classify_query_type("查看表格") == "table"
        assert query_analyzer.classify_query_type("看图") == "image"
        assert query_analyzer.classify_query_type("如何使用") == "general"

    def test_ranking_boost_chart_query(self, modality_retrieval, query_analyzer):
        """Test modality boost for chart query."""
        query = "显示图表"
        analysis = query_analyzer.analyze(query)

        # Mock retrieval results
        retrieval_results = [
            {
                "id": 1,
                "content": "文档文本内容",
                "content_type": "text",
                "score": 0.5,
                "metadata": {},
            },
            {
                "id": 2,
                "content": "表格数据",
                "content_type": "table",
                "score": 0.6,
                "metadata": {},
            },
            {
                "id": 3,
                "content": "图片内容",
                "content_type": "image",
                "score": 0.4,
                "metadata": {},
            },
        ]

        # Apply modality-aware enhancement
        enhanced_results, metadata = modality_retrieval.enhance_retrieval(
            query, retrieval_results
        )

        # For chart query, table and image should be boosted
        assert metadata["needs_chart"] is True

        # Check that table and image results got boosted
        for result in enhanced_results:
            if result.get("content_type") == "table":
                assert result.get("modality_boost", 1.0) > 1.0
            elif result.get("content_type") == "image":
                assert result.get("modality_boost", 1.0) > 1.0
            else:
                # Text might not be boosted
                assert result.get("modality_boost", 1.0) == 1.0

    def test_ranking_boost_general_query(self, modality_retrieval, query_analyzer):
        """Test modality boost for general query."""
        query = "如何使用这个系统"
        analysis = query_analyzer.analyze(query)

        # Mock retrieval results
        retrieval_results = [
            {
                "id": 1,
                "content": "文档内容",
                "content_type": "text",
                "score": 0.7,
                "metadata": {},
            },
            {
                "id": 2,
                "content": "更多内容",
                "content_type": "text",
                "score": 0.6,
                "metadata": {},
            },
        ]

        # Apply modality-aware enhancement
        enhanced_results, metadata = modality_retrieval.enhance_retrieval(
            query, retrieval_results
        )

        # For general query, no special boosting should occur
        assert metadata["needs_chart"] is False
        assert metadata["needs_table"] is False
        assert metadata["needs_image"] is False

        # All results should have neutral boost
        for result in enhanced_results:
            assert result.get("modality_boost", 1.0) == 1.0

    def test_vlm_enhanced_chunks(self, modality_retrieval):
        """Test VLM-enhanced text generation."""
        from unittest.mock import patch
        # Mock VLM enabled setting
        with patch('app.rag.modality_aware_retrieval.settings.vlm_enabled', True):
            # Mock retrieval results with image
            retrieval_results = [
                {
                    "id": 1,
                    "content": "OCR识别的文字",
                    "content_type": "image",
                    "score": 0.8,
                    "metadata": {
                        "vlm_description": "VLM生成的详细图片描述",
                    },
                },
                {
                    "id": 2,
                    "content": "表格数据",
                    "content_type": "table",
                    "score": 0.9,
                    "metadata": {},
                },
            ]

            chunks = modality_retrieval.get_vlm_enhanced_chunks(retrieval_results)

            # First chunk should have VLM enhancement
            assert "VLM" in chunks[0]
            # Second chunk should be unchanged
            assert "VLM" not in chunks[1]

    def test_context_builder_integration(self, modality_retrieval):
        """Test enhanced context builder integration."""
        query = "显示图表"
        retrieval_results = [
            {
                "id": 1,
                "content": "图表数据",
                "content_type": "table",
                "score": 0.8,
            },
        ]

        # Get context builder
        builder = modality_retrieval.get_enhanced_context_builder(
            query, retrieval_results
        )

        # Build context
        context = builder(retrieval_results)

        # Verify context is not empty
        assert context
        assert "[0]" in context

    def test_no_results(self, modality_retrieval, query_analyzer):
        """Test handling of empty retrieval results."""
        query = "测试查询"
        analysis = query_analyzer.analyze(query)

        enhanced_results, metadata = modality_retrieval.enhance_retrieval(
            query, []
        )

        # Should return empty results and metadata
        assert len(enhanced_results) == 0
        assert metadata["original_result_count"] == 0

    def test_multiple_keywords_query(self, query_analyzer):
        """Test query with multiple matching keywords."""
        query = "查看图表、表格和图片"

        analysis = query_analyzer.analyze(query)

        # All three needs should be detected
        assert analysis["needs_chart"] is True
        assert analysis["needs_table"] is True
        assert analysis["needs_image"] is True

        # Check that all confidences are reasonable
        assert analysis["chart_confidence"] > 0.3
        assert analysis["table_confidence"] > 0.3
        assert analysis["image_confidence"] > 0.3
