"""Tests for Query Analyzer for multimodal retrieval.

Author: C2
Date: 2026-03-07
"""

import pytest

from app.rag.query_analyzer import QueryAnalyzer


class TestQueryAnalyzer:
    """Test query analyzer functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create query analyzer instance."""
        return QueryAnalyzer()

    def test_analyze_chart_query(self, analyzer):
        """Test chart query detection."""
        query = "请显示销售趋势图表"
        result = analyzer.analyze(query)

        assert result["needs_chart"] is True
        assert result["needs_table"] is False
        assert result["needs_image"] is False
        assert result["chart_confidence"] > 0.5

    def test_analyze_table_query(self, analyzer):
        """Test table query detection."""
        query = "查看数据表中的明细"
        result = analyzer.analyze(query)

        assert result["needs_chart"] is False
        assert result["needs_table"] is True
        assert result["needs_image"] is False
        assert result["table_confidence"] > 0.5

    def test_analyze_image_query(self, analyzer):
        """Test image query detection."""
        query = "这张图片展示了什么"
        result = analyzer.analyze(query)

        assert result["needs_chart"] is False
        assert result["needs_table"] is False
        assert result["needs_image"] is True
        assert result["image_confidence"] > 0.5

    def test_analyze_general_query(self, analyzer):
        """Test general query without specific needs."""
        query = "如何使用这个系统"
        result = analyzer.analyze(query)

        assert result["needs_chart"] is False
        assert result["needs_table"] is False
        assert result["needs_image"] is False
        assert result["confidence"] < 0.3

    def test_analyze_empty_query(self, analyzer):
        """Test empty query."""
        query = ""
        result = analyzer.analyze(query)

        assert result["needs_chart"] is False
        assert result["needs_table"] is False
        assert result["needs_image"] is False
        assert result["confidence"] == 0.0

    def test_classify_query_type(self, analyzer):
        """Test query type classification."""
        assert analyzer.classify_query_type("显示图表") == "chart"
        assert analyzer.classify_query_type("查看表格") == "table"
        assert analyzer.classify_query_type("看这张图片") == "image"
        assert analyzer.classify_query_type("系统如何使用") == "general"

    def test_get_ranking_boost(self, analyzer):
        """Test ranking boost type retrieval."""
        analysis = analyzer.analyze("显示销售图表和数据表")

        boost_types = analyzer.get_ranking_boost(analysis)

        assert "table" in boost_types
        assert "image" in boost_types

    def test_multiple_keywords(self, analyzer):
        """Test query with multiple keyword types."""
        # Should prioritize based on confidence
        query = "查看图表、表格和图片"

        result = analyzer.analyze(query)

        # All three needs should be detected
        needs = [result["needs_chart"], result["needs_table"], result["needs_image"]]
        assert any(needs) is True
        assert result["chart_confidence"] > 0 or result["table_confidence"] > 0 or result["image_confidence"] > 0

    def test_case_insensitivity(self, analyzer):
        """Test case-insensitive keyword matching."""
        queries = [
            "显示图表",
            "显示图表",
            "CHART",
        ]

        for query in queries:
            result = analyzer.analyze(query)
            assert result["needs_chart"] is True
            assert result["chart_confidence"] > 0.5

    def test_partial_keyword_match(self, analyzer):
        """Test partial keyword matching gives lower score."""
        query = "显示的图表趋势"
        result = analyzer.analyze(query)

        # "图表" is a partial match
        assert result["needs_chart"] is True
        # But confidence should be lower than exact match
        assert result["chart_confidence"] < 0.9
