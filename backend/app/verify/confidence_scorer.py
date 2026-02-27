"""Confidence scorer for answer quality.

Author: C2
Date: 2026-02-27
"""

from dataclasses import dataclass
from typing import List

from app.verify.nli_detector import NLIHallucinationDetector, HallucinationResult


@dataclass
class ConfidenceScore:
    """置信度分数"""
    score: float  # 0.0 - 1.0
    level: str  # "high", "medium", "low"
    reason: str


class ConfidenceScorer:
    """答案置信度评估器.

    基于以下因素计算置信度：
    - NLI 忠实度
    - 检索结果质量
    - 句子数量
    """

    def __init__(self, nli_detector: NLIHallucinationDetector) -> None:
        self.nli_detector = nli_detector

    def score(
        self,
        answer: str,
        context: str,
        retrieval_score: float = 0.0,
    ) -> ConfidenceScore:
        """计算答案置信度.

        Args:
            answer: 答案文本
            context: 参考上下文
            retrieval_score: 检索分数

        Returns:
            置信度结果
        """
        # 使用 NLI 检测忠实度
        result = self.nli_detector.detect(answer, context)
        faithfulness = result.faithfulness_score

        # 综合检索分数和忠实度
        score = 0.7 * faithfulness + 0.3 * min(1.0, retrieval_score)

        level = self._get_level(score)
        reason = f"忠实度: {faithfulness:.2f}, 检索分数: {retrieval_score:.2f}"

        return ConfidenceScore(score=score, level=level, reason=reason)

    def _get_level(self, score: float) -> str:
        """根据分数返回置信度等级."""
        if score >= 0.8:
            return "high"
        elif score >= 0.5:
            return "medium"
        return "low"