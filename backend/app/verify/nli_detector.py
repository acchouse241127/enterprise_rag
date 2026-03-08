"""NLI Hallucination Detector for answer quality assessment.

Author: C2
Date: 2026-02-27
"""

import re
from dataclasses import dataclass
from typing import List

from sentence_transformers import CrossEncoder


@dataclass
class HallucinationResult:
    """幻觉检测结果"""
    faithfulness_score: float  # 忠实度分数
    supported_count: int  # 被支持的句子数
    total_count: int  # 总句子数
    details: List[dict]  # 每个句子的检测详情


class NLIHallucinationDetector:
    """基于 NLI 模型的幻觉检测器。

    使用 cross-encoder/nli-deberta-v3-base 模型，约 700MB，GPU 显存 ~1GB。
    支持自动检测 CUDA 可用性，回退到 CPU 模式。
    """

    MODEL_NAME = "cross-encoder/nli-deberta-v3-base"
    LABELS = ["contradiction", "entailment", "neutral"]

    def __init__(self, device: str = "auto") -> None:
        # 自动检测 CUDA 可用性
        if device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                self.device = "cpu"
        else:
            self.device = device
        self.model = CrossEncoder(self.MODEL_NAME, device=self.device)

    def detect(self, answer: str, context: str) -> HallucinationResult:
        """检测答案相对于上下文的忠实度.

        Args:
            answer: 待检测的答案
            context: 参考上下文（检索到的 chunks）

        Returns:
            忠实度检测结果
        """
        sentences = self._split_sentences(answer)
        if not sentences:
            return HallucinationResult(1.0, 0, 0, [])

        details = []
        supported_count = 0

        for sentence in sentences:
            pairs = [(context, sentence)]
            scores = self.model.predict(pairs)
            label_idx = scores[0].argmax()
            label = self.LABELS[label_idx]
            is_supported = (label == "entailment")
            if is_supported:
                supported_count += 1
            details.append({
                "sentence": sentence,
                "label": label,
                "supported": is_supported,
            })

        total_count = len(sentences)
        faithfulness_score = supported_count / total_count if total_count > 0 else 1.0

        return HallucinationResult(
            faithfulness_score=faithfulness_score,
            supported_count=supported_count,
            total_count=total_count,
            details=details,
        )

    def _split_sentences(self, text: str) -> List[str]:
        """中英文混合句子分割."""
        parts = re.split(r"(?<=[。！？!?\n])\s*", text)
        sentences = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 5]
        return sentences