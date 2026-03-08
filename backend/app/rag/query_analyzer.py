"""Query analyzer for multimodal retrieval enhancement.

Analyzes user queries to detect intent and identify
whether specific modalities (charts, tables, images) are needed.

Author: C2
Date: 2026-03-07
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyzes query intent for modality-aware retrieval.

    Detects when a user query specifically asks for:
    - Charts and visualizations
    - Tables and tabular data
    - Images and diagrams
    """

    # Keywords for different content types
    CHART_KEYWORDS = [
        "图表", "趋势", "曲线", "柱状", "饼图",
        "折线", "折线图", "条形", "直方", "散点",
        "趋势图", "统计图", "可视化", "graph", "chart",
        "柱子图", "饼状图", "线图", "分布图",
    ]

    TABLE_KEYWORDS = [
        "表格", "数据", "列", "行", "对比",
        "table", "数据表", "明细", "列表", "字段",
        "行列", "columns", "rows", "单元格", "cell",
        "tabular", "汇总", "统计表", "清单",
    ]

    IMAGE_KEYWORDS = [
        "图片", "图像", "图示", "示意图", "截图",
        "image", "照片", "插图", "图片显示", "图片展示",
        "图片中", "图中", "图像中", "看图", "见图片",
        "截图显示", "截图如下", "图片说明", "图片说明",
        "image", "photo", "illustration", "figure", "diagram",
        "图表显示", "图表中", "看图表", "见图表",
    ]

    def __init__(self):
        """Initialize query analyzer."""
        self._logger = logger

    def analyze(self, query: str) -> dict[str, Any]:
        """Analyze query and return intent analysis.

        Args:
            query: User query string

        Returns:
            Dict with analysis results:
            - needs_chart: Query asks for charts/visualizations
            - needs_table: Query asks for tables
            - needs_image: Query asks for images
            - confidence: Confidence score for each need
        """
        if not query or not query.strip():
            return {
                "needs_chart": False,
                "needs_table": False,
                "needs_image": False,
                "confidence": 0.0,
            }

        query_lower = query.lower()

        # Analyze for chart needs
        chart_score = self._calculate_need_score(
            query_lower, self.CHART_KEYWORDS
        )

        # Analyze for table needs
        table_score = self._calculate_need_score(
            query_lower, self.TABLE_KEYWORDS
        )

        # Analyze for image needs
        image_score = self._calculate_need_score(
            query_lower, self.IMAGE_KEYWORDS
        )

        # Log analysis
        self._logger.info(
            f"Query analysis - chart: {chart_score:.2f}, "
            f"table: {table_score:.2f}, image: {image_score:.2f}"
        )

        return {
            "needs_chart": chart_score > 0.3,
            "needs_table": table_score > 0.3,
            "needs_image": image_score > 0.3,
            "chart_confidence": chart_score,
            "table_confidence": table_score,
            "image_confidence": image_score,
            "raw_query": query,
        }

    def _calculate_need_score(
        self, query_lower: str, keywords: list[str]
    ) -> float:
        """Calculate need score based on keyword matching.

        Args:
            query_lower: Lowercase query string
            keywords: List of keywords to match

        Returns:
            Score between 0 and 1 indicating likelihood of need
        """
        if not query_lower:
            return 0.0

        # Direct keyword match - higher score
        for keyword in keywords:
            if keyword in query_lower:
                return 0.9  # Strong match

        # Partial match - lower score
        for keyword in keywords:
            if keyword in query_lower.replace(" ", ""):
                return 0.6  # Partial match

        return 0.0

    def classify_query_type(self, query: str) -> str:
        """Classify query into a type category.

        Args:
            query: User query string

        Returns:
            Query type: "chart", "table", "image", "general"
        """
        analysis = self.analyze(query)

        if analysis["needs_chart"]:
            return "chart"
        elif analysis["needs_table"]:
            return "table"
        elif analysis["needs_image"]:
            return "image"
        else:
            return "general"

    def get_ranking_boost(self, analysis: dict[str, Any]) -> list[str]:
        """Get content types to boost based on analysis.

        Args:
            analysis: Query analysis result

        Returns:
            List of content types to boost in ranking
        """
        boost_types = []

        if analysis.get("needs_chart"):
            boost_types.extend(["table", "image"])

        if analysis.get("needs_table"):
            boost_types.append("table")

        if analysis.get("needs_image"):
            boost_types.append("image")

        return boost_types
