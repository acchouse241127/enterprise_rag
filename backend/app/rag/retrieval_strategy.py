"""Retrieval strategy configuration for different use cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RetrievalStrategyName = Literal["default", "high_recall", "high_precision", "low_latency"]


@dataclass
class RetrievalStrategy:
    """Configuration for a retrieval strategy."""

    name: str
    top_k: int
    expansion_enabled: bool
    keyword_enabled: bool
    reranker_candidate_k: int
    description: str = ""


# 预定义策略
STRATEGIES: dict[str, RetrievalStrategy] = {
    "default": RetrievalStrategy(
        name="default",
        top_k=5,
        expansion_enabled=True,
        keyword_enabled=True,
        reranker_candidate_k=12,
        description="默认策略：平衡召回率和响应速度",
    ),
    "high_recall": RetrievalStrategy(
        name="high_recall",
        top_k=8,
        expansion_enabled=True,
        keyword_enabled=True,
        reranker_candidate_k=16,
        description="高召回策略：返回更多结果，适合探索性查询",
    ),
    "high_precision": RetrievalStrategy(
        name="high_precision",
        top_k=4,
        expansion_enabled=False,
        keyword_enabled=False,
        reranker_candidate_k=8,
        description="高精度策略：只返回最相关结果，减少噪音",
    ),
    "low_latency": RetrievalStrategy(
        name="low_latency",
        top_k=4,
        expansion_enabled=False,
        keyword_enabled=False,
        reranker_candidate_k=6,
        description="低延迟策略：最快响应，适合实时场景",
    ),
}


def get_strategy(name: str | None = None) -> RetrievalStrategy:
    """
    Get retrieval strategy by name.

    Args:
        name: Strategy name, defaults to "default" if None or invalid

    Returns:
        RetrievalStrategy configuration
    """
    if name is None or name not in STRATEGIES:
        return STRATEGIES["default"]
    return STRATEGIES[name]


def list_strategies() -> list[dict]:
    """List all available strategies with their configurations."""
    return [
        {
            "name": s.name,
            "top_k": s.top_k,
            "expansion_enabled": s.expansion_enabled,
            "keyword_enabled": s.keyword_enabled,
            "reranker_candidate_k": s.reranker_candidate_k,
            "description": s.description,
        }
        for s in STRATEGIES.values()
    ]
