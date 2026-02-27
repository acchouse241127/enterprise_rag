"""Citation Verifier for reference accuracy.

Author: C2
Date: 2026-02-27
"""

import re
from dataclasses import dataclass

from app.verify.nli_detector import NLIHallucinationDetector


@dataclass
class CitationResult:
    """引用验证结果"""
    cleaned_answer: str  # 清洗后的答案（移除虚假引用）
    citation_accuracy: float  # 引用准确率
    total_citations: int  # 总引用数
    valid_citations: int  # 有效引用数


class CitationVerifier:
    """基于 NLI 的引用准确性验证"""

    CITATION_PATTERN = r"\[ID:(\d+)\]"

    def __init__(self, nli_detector: NLIHallucinationDetector) -> None:
        self.nli_detector = nli_detector

    def verify(self, answer: str, chunks: list) -> CitationResult:
        """验证引用准确性.

        1. 正则解析 answer 中所有 [ID:x] 标记
        2. 提取每个标记所在的句子
        3. 用 NLI 判断：该句子是否被 chunk x 蕴含
        4. 不是 entailment → 移除该 [ID:x]（虚假引用）

        Args:
            answer: 包含引用标记的答案
            chunks: 检索结果 chunks

        Returns:
            验证结果
        """
        citations = re.findall(self.CITATION_PATTERN, answer)
        total_citations = len(citations)

        if not citations:
            return CitationResult(answer, 1.0, 0, 0)

        valid_citations = 0
        cleaned_answer = answer

        for citation in citations:
            # 提取 ID
            try:
                cid = int(citation[3:-1])  # 移除 [ID: 和 ]
            except ValueError:
                continue

            # 找到对应句子
            sentence = self._extract_sentence_with_citation(answer, citation)
            if not sentence:
                continue

            # 检查是否被支持
            is_supported = self._check_support(sentence, chunks, cid)
            if is_supported:
                valid_citations += 1
            else:
                # 移除虚假引用
                cleaned_answer = cleaned_answer.replace(citation, "")

        citation_accuracy = valid_citations / total_citations if total_citations > 0 else 1.0

        return CitationResult(
            cleaned_answer=cleaned_answer,
            citation_accuracy=citation_accuracy,
            total_citations=total_citations,
            valid_citations=valid_citations,
        )

    def _extract_sentence_with_citation(self, answer: str, citation: str) -> str | None:
        """提取包含引用的句子."""
        idx = answer.find(citation)
        if idx == -1:
            return None

        # 向后查找句子结束
        end = idx + len(citation)
        while end < len(answer) and not any(answer[end] in "。！？.!?\n"):
            end += 1

        # 向前查找句子开始
        start = idx
        while start > 0 and not any(answer[start-1] in "。！？.!?\n"):
            start -= 1

        return answer[start:end].strip()

    def _check_support(self, sentence: str, chunks: list, cid: int) -> bool:
        """检查句子是否被 chunk 支持."""
        # 简化实现：检查句子是否在对应 chunk 中
        for chunk in chunks:
            if chunk.get("chunk_index") == cid:
                # 使用 NLI 检测是否支持
                result = self.nli_detector.detect(sentence, chunk.get("content", ""))
                return result.faithfulness_score > 0.5
        return False