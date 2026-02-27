"""Adaptive top-k selection based on score cliff detection.

Author: C2
Date: 2026-02-27

Reference: TRD 4.4
"""

import statistics
from typing import List

from app.rag.parent_retriever import RetrievalResult


class AdaptiveTopK:
    """基于分数断崖检测的自适应 Top-K。

    算法：
    1. 提取分数序列：scores = [r.score for r in results]
    2. 计算相邻差值：diffs = [scores[i] - scores[i+1] for i in range(len-1)]
    3. 计算 μ = mean(diffs), σ = std(diffs)
    4. 找到第一个 i 使得 diffs[i] > μ + cliff_factor * σ
    5. 截断点 = min(max(i+1, min_k), max_k)
    6. 返回 results[:截断点]
    """

    def __init__(
        self,
        min_k: int = 2,
        max_k: int = 15,
        cliff_factor: float = 1.5,
    ) -> None:
        if min_k <= 0:
            raise ValueError("min_k must be greater than 0")
        if max_k <= min_k:
            raise ValueError("max_k must be greater than min_k")
        if cliff_factor <= 0:
            raise ValueError("cliff_factor must be greater than 0")

        self.min_k = min_k
        self.max_k = max_k
        self.cliff_factor = cliff_factor

    def select(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """选择自适应的 Top-K 结果。

        Args:
            results: 按分数降序排序的检索结果

        Returns:
            截断后的结果列表
        """
        if len(results) <= self.min_k:
            return results

        # 提取分数
        scores = [r.score for r in results]

        # 计算相邻差值
        diffs = [scores[i] - scores[i+1] for i in range(len(scores) - 1)]

        if not diffs or all(d == 0 for d in diffs):
            return results[:self.min_k]

        # 计算均值和标准差
        try:
            mean_diff = statistics.mean(diffs)
            std_diff = statistics.stdev(diffs) if len(diffs) > 1 else 0
        except statistics.StatisticsError:
            return results[:self.min_k]

        if std_diff == 0:
            return results[:self.min_k]

        # 找到第一个断崖点
        threshold = mean_diff + self.cliff_factor * std_diff
        cliff_index = None
        for i, diff in enumerate(diffs):
            if diff > threshold:
                cliff_index = i
                break

        # 确保截断点在 [min_k, max_k] 范围内
        if cliff_index is None:
            truncate_k = self.min_k
        else:
            truncate_k = max(cliff_index + 1, self.min_k)

        truncate_k = min(truncate_k, len(results))
        truncate_k = min(truncate_k, self.max_k)

        return results[:truncate_k]