"""Verification Pipeline for answer quality check.

Author: C2
Date: 2026-02-27
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Literal

from app.verify.nli_detector import NLIHallucinationDetector, HallucinationResult
from app.verify.confidence_scorer import ConfidenceScorer, ConfidenceScore
from app.verify.citation_verifier import CitationVerifier, CitationResult


class VerificationAction(Enum):
    """验证动作类型"""
    PASS = "pass"        # 直接通过
    FILTER = "filter"     # 过滤内容
    RETRY = "retry"       # 重新生成
    REFUSE = "refuse"     # 拒答


@dataclass
class VerificationResult:
    """验证结果"""
    action: VerificationAction
    confidence_score: ConfidenceScore | None
    citation_result: CitationResult | None
    refusal_message: str | None
    reason: str


class VerifyPipeline:
    """答案验证 Pipeline.

    流程：
    1. 检测忠实度
    2. 计算置信度
    3. 引用验证
    4. 决策 PASS/FILTER/RETRY/REFUSE
    """

    def __init__(
        self,
        nli_detector: NLIHallucinationDetector,
        confidence_threshold: float = 0.5,
        citation_threshold: float = 0.5,
        refusal_threshold: float = 0.3,
    ) -> None:
        self.nli_detector = nli_detector
        self.confidence_threshold = confidence_threshold
        self.citation_threshold = citation_threshold
        self.refusal_threshold = refusal_threshold

    def verify(
        self,
        answer: str,
        contexts: List[str],
        retrieval_score: float = 0.0,
    ) -> VerificationResult:
        """完整验证流程.

        Args:
            answer: 答案
            contexts: 参考上下文（检索到的 chunks）
            retrieval_score: 平均检索分数

        Returns:
            验证结果
        """
        # 合并所有 contexts
        context = "\n\n".join(contexts)

        # 1. NLI 检测
        hallucination_result = self.nli_detector.detect(answer, context)

        # 2. 置信度计算
        scorer = ConfidenceScorer(self.nli_detector)
        confidence_result = scorer.score(answer, context, retrieval_score)

        # 3. 引用验证
        verifier = CitationVerifier(self.nli_detector)
        citation_result = verifier.verify(answer, contexts)

        # 4. 决策
        return self._decide(
            hallucination_result,
            confidence_result,
            citation_result,
        )

    def _decide(
        self,
        hallucination: HallucinationResult,
        confidence: ConfidenceScore,
        citation: CitationResult,
    ) -> VerificationResult:
        """决策验证动作."""
       忠诚度 = hallucination.faithfulness_score
        置信度 = confidence.score
        引用准确度 = citation.citation_accuracy

        # 检查是否拒答
        if 置信度 < self.refusal_threshold or 忠诚度 < self.refusal_threshold:
            return VerificationResult(
                action=VerificationAction.REFUSE,
                confidence_score=confidence,
                citation_result=citation,
                refusal_message="根据现有知识库内容，无法提供可靠答案。",
                reason=f"低置信度: {置信度:.2f}",
            )

        # 检查引用准确性
        if 引用准确度 < self.citation_threshold:
            return VerificationResult(
                action=VerificationAction.FILTER,
                confidence_score=confidence,
                citation_result=citation,
                refusal_message=None,
                reason=f"引用准确度不足: {引用准确度:.2f}",
            )

        # 通过
        return VerificationResult(
            action=VerificationAction.PASS,
            confidence_score=confidence,
            citation_result=citation,
            refusal_message=None,
            reason=f"通过: 置信度=.{置信度:.2f}, 引用准确度={引用准确度:.2f}",
        )