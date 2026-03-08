"""Retrieval strategy configuration for different use cases.

V2.0 混合方案：
- 普通用户：只选策略，内置最优配置
- 高级用户：展开高级选项，可覆盖内置配置
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RetrievalStrategyName = Literal["smart", "precise", "fast", "deep", "enhanced"]
ExpansionMode = Literal["rule", "llm", "hybrid", "none"]
RetrievalMode = Literal["vector", "bm25", "hybrid"]


@dataclass
class RetrievalStrategy:
    """Configuration for a retrieval strategy.

    V2.0 新增字段：
    - display_name: 中文显示名（面向用户）
    - expansion_mode: 内置查询扩展模式
    - retrieval_mode: 内置检索模式
    """

    name: str
    display_name: str
    top_k: int
    expansion_enabled: bool
    expansion_mode: ExpansionMode
    keyword_enabled: bool
    retrieval_mode: RetrievalMode
    reranker_candidate_k: int
    description: str = ""


# 预定义策略（V2.0 混合方案）
STRATEGIES: dict[str, RetrievalStrategy] = {
    "smart": RetrievalStrategy(
        name="smart",
        display_name="智能（推荐）",
        top_k=8,
        expansion_enabled=True,
        expansion_mode="hybrid",
        keyword_enabled=True,
        retrieval_mode="hybrid",
        reranker_candidate_k=20,
        description="平衡召回与精度，适合大多数场景",
    ),
    "precise": RetrievalStrategy(
        name="precise",
        display_name="精准",
        top_k=5,
        expansion_enabled=False,
        expansion_mode="none",
        keyword_enabled=False,
        retrieval_mode="hybrid",
        reranker_candidate_k=12,
        description="优先答案准确性，减少噪音",
    ),
    "fast": RetrievalStrategy(
        name="fast",
        display_name="快速",
        top_k=4,
        expansion_enabled=False,
        expansion_mode="none",
        keyword_enabled=False,
        retrieval_mode="vector",
        reranker_candidate_k=8,
        description="优先响应速度，适合实时场景",
    ),
    "deep": RetrievalStrategy(
        name="deep",
        display_name="深度",
        top_k=12,
        expansion_enabled=True,
        expansion_mode="llm",
        keyword_enabled=True,
        retrieval_mode="hybrid",
        reranker_candidate_k=30,
        description="最大召回范围，适合探索性查询",
    ),
    "enhanced": RetrievalStrategy(
        name="enhanced",
        display_name="增强（多模态）",
        top_k=8,
        expansion_enabled=True,
        expansion_mode="hybrid",
        keyword_enabled=True,
        retrieval_mode="hybrid",
        reranker_candidate_k=20,
        description="多模态感知检索，针对图表、表格、图片优化",
    ),
}


def get_strategy(name: str | None = None) -> RetrievalStrategy:
    """
    Get retrieval strategy by name.

    Args:
        name: Strategy name, defaults to "smart" if None or invalid

    Returns:
        RetrievalStrategy configuration
    """
    if name is None or name not in STRATEGIES:
        return STRATEGIES["smart"]
    return STRATEGIES[name]


def list_strategies() -> list[dict]:
    """List all available strategies with their configurations."""
    return [
        {
            "name": s.name,
            "display_name": s.display_name,
            "top_k": s.top_k,
            "expansion_enabled": s.expansion_enabled,
            "expansion_mode": s.expansion_mode,
            "keyword_enabled": s.keyword_enabled,
            "retrieval_mode": s.retrieval_mode,
            "reranker_candidate_k": s.reranker_candidate_k,
            "description": s.description,
        }
        for s in STRATEGIES.values()
    ]
