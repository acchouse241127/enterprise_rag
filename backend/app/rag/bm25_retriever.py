"""BM25 retriever using PostgreSQL FTS with pg_jieba.

Author: C2
Date: 2026-02-27
"""

from dataclasses import dataclass
from typing import Literal

import jieba
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


@dataclass
class BM25Result:
    """BM25 检索结果"""
    id: str
    document_id: int
    knowledge_base_id: int
    chunk_index: int
    content: str
    section_title: str | None
    metadata: dict
    bm25_score: float


class BM25Retriever:
    """BM25 retriever using PostgreSQL FTS + pg_jieba."""

    def __init__(self) -> None:
        jieba.initialize()

    def _build_tsquery(self, query: str) -> str:
        """将查询文本转换为 PostgreSQL tsquery 对象。

        策略：
        - 中文文本：使用 jieba 分词，用 & 连接（AND 语义）
        - 英文文本：使用 simple 配制，用 & 连接
        - 中英混合：分别处理，用 & 连接

        安全：移除所有 SQL 特殊操作符和 tsquery 运算符
        """
        import re
        words = []
        for token in jieba.cut(query, cut_all=False):
            token = token.strip()
            if not token:
                continue
            # 移除所有 tsquery 特殊字符和 SQL 操作符
            cleaned = re.sub(r'[&|!\(\):<>]', '', token).strip()
            if not cleaned or len(cleaned) < 1:
                continue
            words.append(cleaned)
        if not words:
            return ""
        # 使用 & 连接，确保所有词都匹配（提高准确度）
        return " & ".join(words)

    def search(
        self,
        query: str,
        knowledge_base_id: int,
        top_k: int = 10,
    ) -> tuple[list[BM25Result], str | None]:
        """BM25 检索。

        Args:
            query: 用户查询文本
            knowledge_base_id: 知识库 ID
            top_k: 返回结果数量

        Returns:
            (BM25Result 列表, 错误信息)
        """
        cleaned = query.strip()
        if not cleaned:
            return [], "query 不能为空"

        tsquery = self._build_tsquery(cleaned)
        if not tsquery:
            return [], "query 解析失败"

        sql = text("""
            SELECT
                id,
                document_id,
                knowledge_base_id,
                chunk_index,
                content,
                section_title,
                metadata,
                ts_rank_cd(content_tsv, to_tsquery('jieba', :tsquery)) AS bm25_score
            FROM chunks
            WHERE
                knowledge_base_id = :kb_id
                AND content_tsv IS NOT NULL
                AND content_tsv @@ to_tsquery('jieba', :tsquery)
            ORDER BY bm25_score DESC
            LIMIT :top_k
        """)

        db: Session
        with SessionLocal() as db:
            try:
                result = db.execute(sql, {"kb_id": knowledge_base_id, "tsquery": tsquery, "top_k": top_k})
                rows = result.all()

                bm25_results: list[BM25Result] = []
                for row in rows:
                    try:
                        bm25_results.append(BM25Result(
                            id=str(row[0]) if row[0] is not None else "",
                            document_id=int(row[1]) if row[1] is not None else 0,
                            knowledge_base_id=int(row[2]) if row[2] is not None else 0,
                            chunk_index=int(row[3]) if row[3] is not None else 0,
                            content=str(row[4]) if row[4] is not None else "",
                            section_title=str(row[5]) if row[5] is not None else None,
                            metadata=dict(row[6]) if isinstance(row[6], dict) else {},
                            bm25_score=float(row[7]) if row[7] is not None else 0.0,
                        ))
                    except (ValueError, TypeError) as e:
                        continue  # 跳过格式错误的数据行

                return bm25_results, None
            except Exception as e:
                return [], f"BM25 检索失败: {e}"