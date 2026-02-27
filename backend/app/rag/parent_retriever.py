"""Parent document retrieval for hybrid search.

Author: C2
Date: 2026-02-27
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


@dataclass
class RetrievalResult:
    """检索结果"""
    id: str
    document_id: int
    knowledge_base_id: int
    chunk_index: int
    content: str
    section_title: str | None
    metadata: dict
    score: float
    is_parent: bool = False


class ParentRetriever:
    """父文档检索器，支持 physical 和 dynamic 两种模式。

    physical 模式：
    - 检索 Child chunks，返回对应的 Parent chunks
    - 需要文档处理时生成双层 chunks

    dynamic 模式：
    - 检索单个 chunk，动态扩展相邻 chunks
    - 无需重新索引，灵活性高

    off 模式：
    - 不进行父文档扩展
    """

    async def retrieve(
        self,
        hits: list[RetrievalResult],
        mode: Literal["physical", "dynamic", "off"] = "dynamic",
        dynamic_expand_n: int = 2,
    ) -> list[RetrievalResult]:
        """父文档扩展。

        Args:
            hits: 初始检索结果
            mode: 父文档模式
            dynamic_expand_n: dynamic 模式下扩展数量

        Returns:
            扩展后的检索结果
        """
        if mode == "off":
            return hits
        if mode == "physical":
            return await self._physical_expand(hits)
        if mode == "dynamic":
            return await self._dynamic_expand(hits, dynamic_expand_n)
        return hits

    async def _physical_expand(self, hits: list[RetrievalResult]) -> list[RetrievalResult]:
        """物理双层模式：返回 Parent chunks。

        1. 通过 parent_chunk_id 查找 Parent chunk
        2. 去重（多个 Child 可能属于同一 Parent）
        """
        if not hits:
            return []

        parent_ids = [h.metadata.get("parent_chunk_id") for h in hits if h.metadata.get("parent_chunk_id")]
        if not parent_ids:
            return hits

        db: Session
        with SessionLocal() as db:
            sql = text("""
                SELECT id, document_id, knowledge_base_id, chunk_index,
                       content, section_title, metadata, is_parent
                FROM chunks
                WHERE id = ANY(:ids)
                AND is_parent = true
            """)
            result = db.execute(sql, {"ids": parent_ids})
            rows = result.all()

            parent_map: dict[str, RetrievalResult] = {}
            for row in rows:
                parent_map[str(row[0])] = RetrievalResult(
                    id=str(row[0]),
                    document_id=int(row[1]),
                    knowledge_base_id=int(row[2]),
                    chunk_index=int(row[3]),
                    content=row[4],
                    section_title=row[5],
                    metadata=row[6] or {},
                    score=0.0,
                    is_parent=True,
                )

            # 按 hits 的顺序返回，并去重
            seen_ids = set()
            final_results: list[RetrievalResult] = []
            for hit in hits:
                parent_id = hit.metadata.get("parent_chunk_id")
                if parent_id and str(parent_id) in parent_map and str(parent_id) not in seen_ids:
                    final_results.append(parent_map[str(parent_id)])
                    seen_ids.add(str(parent_id))

            return final_results or hits

    async def _dynamic_expand(
        self,
        hits: list[RetrievalResult],
        expand_n: int = 2,
    ) -> list[RetrievalResult]:
        """动态扩展模式：扩展相邻 chunks。

        对每个命中的 chunk，扩展其前后 n 个同文档 chunk。
        """
        if not hits:
            return []

        document_ids = {h.document_id for h in hits if hasattr(h, "document_id")}
        if not document_ids:
            return hits

        db: Session
        with SessionLocal() as db:
            # 查询所有相关文档的 chunks（按 chunk_index 排序）
            sql = text("""
                SELECT id, document_id, knowledge_base_id, chunk_index,
                       content, section_title, metadata, is_parent
                FROM chunks
                WHERE document_id = ANY(:doc_ids)
                ORDER BY document_id, chunk_index
            """)
            result = db.execute(sql, {"doc_ids": list(document_ids)})
            rows = result.all()

            # 按 document_id 组织 chunks
            doc_chunks: dict[int, list[tuple]] = {}
            for row in rows:
                doc_id = int(row[1])
                if doc_id not in doc_chunks:
                    doc_chunks[doc_id] = []
                doc_chunks[doc_id].append(row)

            # 对每个 hit 扩展
            expanded_results: list[RetrievalResult] = []
            for hit in hits:
                if not hasattr(hit, "document_id") or not hasattr(hit, "chunk_index"):
                    expanded_results.append(hit)
                    continue

                doc_id = hit.document_id
                chunk_index = hit.chunk_index

                if doc_id not in doc_chunks:
                    expanded_results.append(hit)
                    continue

                chunks = doc_chunks[doc_id]
                # 找到当前 chunk 的位置
                current_idx = None
                for idx, chunk in enumerate(chunks):
                    if chunk[3] == chunk_index:  # chunk_index
                        current_idx = idx
                        break

                if current_idx is None:
                    expanded_results.append(hit)
                    continue

                # 扩展前后各 n 个
                start_idx = max(0, current_idx - expand_n)
                end_idx = min(len(chunks), current_idx + expand_n + 1)

                for idx in range(start_idx, end_idx):
                    row = chunks[idx]
                    expanded_results.append(RetrievalResult(
                        id=str(row[0]),
                        document_id=int(row[1]),
                        knowledge_base_id=int(row[2]),
                        chunk_index=int(row[3]),
                        content=row[4],
                        section_title=row[5],
                        metadata=row[6] or {},
                        score=hit.score,
                        is_parent=bool(row[7]),
                    ))

            return expanded_results