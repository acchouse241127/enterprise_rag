"""Hybrid retrieval pipeline for V2.0.

Author: C2
Date: 2026-02-27
"""

import asyncio
import time
from typing import List

from app.rag.bm25_retriever import BM25Retriever
from app.rag.parent_retriever import ParentRetriever, RetrievalResult
from app.rag.reranker import BgeRerankerService
from app.rag.retriever import VectorRetriever
from app.rag.rrf_fusion import RRFFusion
from app.rag.adaptive_topk import AdaptiveTopK
from app.rag.denoiser import Denoiser


class HybridRetrievalPipeline:
    """混合检索管道：BM25 + 向量 → RRF → 父文档 → Reranker → 自适应 → 去噪"""

    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        vector_retriever: VectorRetriever,
        rrf_fusion: RRFFusion,
        parent_retriever: ParentRetriever,
        adaptive_topk: AdaptiveTopK,
        denoiser: Denoiser,
        reranker: BgeRerankerService,
    ):
        self.bm25_retriever = bm25_retriever
        self.vector_retriever = vector_retriever
        self.rrf_fusion = rrf_fusion
        self.parent_retriever = parent_retriever
        self.adaptive_topk = adaptive_topk
        self.denoiser = denoiser
        self.reranker = reranker

    async def retrieve(
        self,
        query: str,
        knowledge_base_id: int,
        top_k: int = 5,
        parent_retrieval_mode: str = "dynamic",
        dynamic_expand_n: int = 2,
        enable_adaptive: bool = True,
        enable_denoise: bool = True,
    ) -> tuple[List[RetrievalResult], dict]:
        """完整检索流程。

        Args:
            query: 查询文本
            knowledge_base_id: 知识库 ID
            top_k: 返回结果数量
            parent_retrieval_mode: 父文档模式
            dynamic_expand_n: dynamic 模式扩展数量
            enable_adaptive: 是否启用自适应深度
            enable_denoise: 是否启用去噪

        Returns:
            (检索结果, 延迟统计)
        """
        latency = {}

        # BM25 + 向量并行检索
        t0 = time.perf_counter()
        bm25_results, _ = await asyncio.to_thread(
            self.bm25_retriever.search, query, knowledge_base_id, top_k * 2
        )
        vector_results, _ = await asyncio.to_thread(
            self.vector_retriever.retrieve, knowledge_base_id, query, top_k * 2
        )
        latency["bm25_ms"] = latency["vector_ms"] = int((time.perf_counter() - t0) * 1000)

        # 将 BM25Result 和 Vector 结果转换为统一格式
        bm25_dicts = [
            {
                "id": r.id,
                "document_id": r.document_id,
                "knowledge_base_id": r.knowledge_base_id,
                "chunk_index": r.chunk_index,
                "content": r.content,
                "section_title": r.section_title,
                "metadata": r.metadata,
                "bm25_score": r.bm25_score,
            }
        for r in bm25_results
        ]
        vector_dicts = vector_results

        # RRF 融合
        t0 = time.perf_counter()
        rrf_results = self.rrf_fusion.fuse([bm25_dicts, vector_dicts], ["bm25", "vector"], top_k=top_k * 2)
        # 将 RRFResult 转换为 RetrievalResult
        fused = [
            RetrievalResult(
                id=r.id,
                document_id=r.document_id,
                knowledge_base_id=r.knowledge_base_id,
                chunk_index=r.chunk_index,
                content=r.content,
                section_title=r.section_title,
                metadata=r.metadata,
                score=r.rrf_score,
            )
        for r in rrf_results
        ]
        latency["rrf_ms"] = int((time.perf_counter() - t0) * 1000)

        # 父文档扩展
        t0 = time.perf_counter()
        expanded = await self.parent_retriever.retrieve(
            fused, mode=parent_retrieval_mode, dynamic_expand_n=dynamic_expand_n
        )
        latency["parent_expand_ms"] = int((time.perf_counter() - t0) * 1000)

        # Reranker 重排序
        t0 = time.perf_counter()
        # 将 RetrievalResult 转换为 Reranker 可用格式
        rerank_dicts = [
            {
                "id": r.id,
                "content": r.content,
            }
            for r in expanded
        ]
        reranked_results = self.reranker.rerank(query, rerank_dicts, top_n=top_k * 2)
        # 重新转换为 RetrievalResult
        reranked = []
        for rerank_result in reranked_results:
            for r in expanded:
                if r.id == rerank_result.get("id", ""):
                    reranked.append(RetrievalResult(
                        id=r.id,
                        document_id=r.document_id,
                        knowledge_base_id=r.knowledge_base_id,
                        chunk_index=r.chunk_index,
                        content=r.content,
                        section_title=r.section_title,
                        metadata=r.metadata,
                        score=rerank_result.get("rerank_score", r.score),
                    ))
                    break
        latency["reranker_ms"] = int((time.perf_counter() - t0) * 1000)

        # 自适应深度截断
        t0 = time.perf_counter()
        truncated = self.adaptive_topk.select(reranked) if enable_adaptive else reranked[:top_k]
        latency["adaptive_topk_ms"] = int((time.perf_counter() - t0) * 1000)

        # 去噪过滤
        t0 = time.perf_counter()
        final = self.denoiser.denoise(query, truncated) if enable_denoise else truncated
        latency["denoise_ms"] = int((time.perf_counter() - t0) * 1000)

        return final[:top_k], latency