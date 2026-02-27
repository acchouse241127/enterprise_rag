"""
Retrieval log and feedback models.

Phase 3.2: 检索日志与用户反馈
Author: C2
Date: 2026-02-13
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float, JSON, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FeedbackType(str, Enum):
    """User feedback type."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


class RetrievalLog(Base):
    """
    Log of each QA retrieval.
    Records query, retrieved chunks, scores, and timing for quality analysis.
    """

    __tablename__ = "retrieval_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    knowledge_base_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_embedding_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retrieval_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rerank_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunks_retrieved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_after_filter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_after_dedup: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_after_rerank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_chunk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_chunk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_chunk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # JSON: [{chunk_id, content_preview, score, document_id}, ...]
    chunk_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # B4.6: 被引用的 chunk IDs（从 answer 中解析 [ID:x] 得到）
    cited_chunk_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    answer_generated: Mapped[bool] = mapped_column(Integer, nullable=False, default=True)  # 是否生成了答案
    answer_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now(), index=True
    )
    # V2.0: 质量指标
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    faithfulness_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    refusal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    refusal_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    feedbacks = relationship("RetrievalFeedback", back_populates="retrieval_log", cascade="all, delete-orphan")


class RetrievalFeedback(Base):
    """
    User feedback on retrieval results.
    Supports helpful/not_helpful marking and optional comments.
    V2.0: 新增 rating (1/-1) 和 reason 字段
    """

    __tablename__ = "retrieval_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    retrieval_log_id: Mapped[int] = mapped_column(
        ForeignKey("retrieval_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # 兼容旧字段
    feedback_type: Mapped[str] = mapped_column(String(20), nullable=True)  # helpful / not_helpful
    # V2.0: 新增强制评分和原因字段
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 (thumbs_up) / -1 (thumbs_down)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # 用户输入的原因
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_sample_marked: Mapped[bool] = mapped_column(Integer, nullable=False, default=False)  # 是否标记为问题样本
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )

    # Relationship
    retrieval_log = relationship("RetrievalLog", back_populates="feedbacks")
