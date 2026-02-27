"""Smart refusal handler for low-confidence answers.

Author: C2
Date: 2026-02-27
"""

from dataclasses import dataclass
from typing import Literal

from app.verify.verify_pipeline import VerificationAction


@dataclass
class RefusalInfo:
    """拒答信息"""
    reason: Literal["empty_retrieval", "low_relevance", "low_confidence", "low_faithfulness"]
    message: str


class RefusalHandler:
    """智能拒答处理器"""

    DEFAULT_MESSAGE = (
        "根据现有知识库内容，无法为您提供可靠的回答。\n\n"
        "建议：\n"
        "1. 尝试换一种方式提问\n"
        "2. 确认相关文档是否已上传到知识库"
    )

    REASON_MESSAGES = {
        "empty_retrieval": "知识库中未找到与您问题相关的内容",
        "low_relevance": "检索到的内容与您的问题关联度较低",
        "low_confidence": "系统对该答案的置信度不足",
        "low_faithfulness": "答案可能包含与知识库不一致的内容",
    }

    def handle(
        self,
        reason: str,
        refusal_threshold: float = 0.3,
    ) -> RefusalInfo:
        """处理拒答。

        Args:
            reason: 拒答原因
            refusal_threshold: 拒答阈值

        Returns:
            拒答信息
        """
        message = (
            f"\n拒绝原因: {self.REASON_MESSAGES.get(reason, '未知原因')}\n"
            f"系统拒绝阈值: {refusal_threshold}\n"
            f"建议: {self._get_suggestion(reason)}"
        )

        return RefusalInfo(reason=reason, message=message)

    def _get_suggestion(self, reason: str) -> str:
        """根据原因获取建议."""
        suggestions = {
            "empty_retrieval": "确认知识库有文档并已成功解析",
            "low_relevance": "尝试提供更多上下文信息",
            "low_confidence": "重新组织语言提问",
            "low_faithfulness": "仅依赖知识库内容回答",
        }
        return suggestions.get(reason, "请尝试其他问题")