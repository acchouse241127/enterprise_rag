"""RRF (Reciprocal Rank Fusion) for hybrid retrieval.

Author: C2
Date: 2026-02-27
"""

from dataclasses import dataclass


@dataclass
class RRFResult:
    """RRF 融合结果"""
    id: str
    document_id: int
    knowledge_base_id: int
    chunk_index: int
    content: str
    section_title: str | None
    metadata: dict
    rrf_score: float
    original_scores: dict[str, float]


class RRFFusion:
    """Reciprocal Rank Fusion: 融合多个检索器的结果。

    RRF 公式：
    rrf_score = sum(1 / (k + rank_i)) for each source i

    其中 k 是平滑因子，rank_i 是该结果在源 i 中的排名（从1开始）。

    优势：
    - 对不同分数尺度不敏感
    - 简单高效
    - 不需要归一化

    参考：Cormack, Clarke, and BUEN (2009)
    """

    def __init__(self, k: int = 60):
        """
        Args:
            k: 平滑因子。默认 60 是推荐值。
               较小的 k（如 10）更偏向顶部结果
               较大的 k（如 100）更偏向多样性
        """
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k

    def fuse(
        self,
        results_list: list[list[dict]],
        source_names: list[str],
        top_k: int = 10,
    ) -> list[RRFResult]:
        """融合多个检索结果列表。

        Args:
            results_list: 多个检索结果列表，每个格式为 [{id, content, score, ...}, ...]
            source_names: 对应每个结果列表的源名称
            top_k: 返回的融合结果数量

        Returns:
            融合后的结果列表，按 rrf_score 降序排列
        """
        if len(results_list) != len(source_names):
            raise ValueError("results_list 和 source_names 长度必须相同")

        if not results_list:
            return []

        scores: dict[str, list[tuple[int, float]]] = {}

        for results, source_name in zip(results_list, source_names):
            for rank, result in enumerate(results, start=1):
                chunk_id = result.get("id") or result.get("chunk_id")
                if not chunk_id:
                    continue

                original_score = result.get("score") or result.get("bm25_score") or result.get("distance", 0.0)
                if chunk_id not in scores:
                    scores[chunk_id] = []

                scores[chunk_id].append((rank, original_score))

        rrf_results: list[RRFResult] = []
        for chunk_id, rankings in scores.items():
            rrf_score = sum(1.0 / (self.k + rank) for rank, _ in rankings)

            first_result = None
            for results in results_list:
                for r in results:
                    if r.get("id") or r.get("chunk_id") == chunk_id:
                        first_result = r
                        break
                if first_result:
                    break

            if not first_result:
                continue

            original_scores_dict = {}
            for idx, (rank, score) in enumerate(rankings):
                source_name = source_names[idx]
                original_scores_dict[source_name] = score

            rrf_result = RRFResult(
                id=chunk_id,
                document_id=int(first_result.get("document_id", 0)),
                knowledge_base_id=int(first_result.get("knowledge_base_id", 0)),
                chunk_index=int(first_result.get("chunk_index", 0)),
                content=first_result.get("content", ""),
                section_title=first_result.get("section_title"),
                metadata=first_result.get("metadata", {}),
                rrf_score=rrf_score,
                original_scores=original_scores_dict,
            )
            rrf_results.append(rrf_result)

        rrf_results.sort(key=lambda x: x.rrf_score, reverse=True)

        return rrf_results[:top_k]

    def fuse_dict(
        self,
        results_dict: dict[str, list[dict]],
        top_k: int = 10,
    ) -> list[RRFResult]:
        """使用字典形式融合多个检索结果。

        Args:
            results_dict: {source_name: [result_dict, ...]}
            top_k: 返回的融合结果数量

        Returns:
            融合后的结果列表，按 rrf_score 降序排列
        """
        source_names = list(results_dict.keys())
        results_list = list(results_dict.values())
        return self.fuse(results_list, source_names, top_k)