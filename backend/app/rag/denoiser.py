"""Denoiser for filtering low-relevance retrieval results.

Author: C2
Date: 2026-02-27

Reference: TRD 4.5
"""

import jieba
from typing import List

from app.rag.parent_retriever import RetrievalResult


class Denoiser:
    """检索结果去噪器。

    双重过滤：
    1. Reranker 分数过滤：score < threshold 的移除
    2. 关键词重叠过滤：
       - 用 jieba 提取 query 的关键词集合 Q
       - 用 jieba 提取 chunk 的关键词集合 C
       - overlap = |Q ∩ C| / |Q|
       - overlap < keyword_overlap_min 的移除
    """

    def __init__(
        self,
        reranker_threshold: float = 0.15,
        keyword_overlap_min: float = 0.2,
    ) -> None:
        if reranker_threshold < 0 or reranker_threshold > 1:
            raise ValueError("reranker_threshold must be between 0 and 1")
        if keyword_overlap_min < 0 or keyword_overlap_min > 1:
            raise ValueError("keyword_overlap_min must be between 0 and 1")

        self.reranker_threshold = reranker_threshold
        self.keyword_overlap_min = keyword_overlap_min

    def denoise(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> List[RetrievalResult]:
        """过滤低相关性的检索结果。

        Args:
            query: 查询文本
            results: 检索结果（按分数降序）

        Returns:
            过滤后的结果
        """
        if not results:
            return []

        # 阶段1：Reranker 分数过滤
        filtered = [
            r for r in results
            if r.score >= self.reranker_threshold
        ]

        if not filtered:
            return []

        # 阶段2：关键词重叠过滤
        try:
            query_keywords = set(jieba.cut(query, cut_all=False))
            query_keywords = {k for k in query_keywords if k.strip()}
        except Exception:
            return filtered

        if not query_keywords:
            return filtered

        final_results: List[RetrievalResult] = []
        for result in filtered:
            try:
                chunk_keywords = set(jieba.cut(result.content, cut_all=False))
                chunk_keywords = {k for k in chunk_keywords if k.strip()}
            except Exception:
                continue

            if not chunk_keywords:
                continue

            overlap = len(query_keywords & chunk_keywords) / len(query_keywords)
            if overlap >= self.keyword_overlap_min:
                final_results.append(result)

        return final_results