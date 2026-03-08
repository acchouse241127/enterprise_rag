"""
Retrieval log service.

Phase 3.2: 检索日志记录与用户反馈
Author: C2
Date: 2026-02-13
"""

from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RetrievalLog, RetrievalFeedback, FeedbackType


class RetrievalLogService:
    """Service for retrieval logging and feedback."""

    # ========== 日志记录 ==========

    @staticmethod
    def create_log(
        db: Session,
        knowledge_base_id: int | None,
        user_id: int | None,
        query: str,
        chunks_retrieved: int = 0,
        chunks_after_filter: int = 0,
        chunks_after_dedup: int = 0,
        chunks_after_rerank: int = 0,
        top_chunk_score: float | None = None,
        avg_chunk_score: float | None = None,
        min_chunk_score: float | None = None,
        chunk_details: list[dict] | None = None,
        cited_chunk_ids: list[int] | None = None,  # B4.6: 被引用的 chunk IDs
        query_embedding_time_ms: int | None = None,
        retrieval_time_ms: int | None = None,
        rerank_time_ms: int | None = None,
        total_time_ms: int | None = None,
        llm_time_ms: int | None = None,
        answer_generated: bool = True,
        answer_length: int | None = None,
        error_message: str | None = None,
        # V2.0 质量保障字段
        confidence_score: float | None = None,
        faithfulness_score: float | None = None,
        has_hallucination: bool | None = None,
        retrieval_mode: str | None = None,
        refusal_reason: str | None = None,
        refusal_message: str | None = None,
        citation_accuracy: float | None = None,
        latency_breakdown: dict | None = None,
    ) -> RetrievalLog:
        """Create a retrieval log entry with V2.0 quality metrics."""
        # Trim chunk_details if too many
        if chunk_details and len(chunk_details) > settings.retrieval_log_max_chunks:
            chunk_details = chunk_details[:settings.retrieval_log_max_chunks]

        # answer_generated 在 DB 中为 INTEGER(0/1)，需显式转换避免 PostgreSQL 类型不匹配
        answer_gen_int = 1 if answer_generated else 0
        
        # V2.0: 转换布尔值为整数
        has_hallucination_int = 1 if has_hallucination else (0 if has_hallucination is False else None)
        
        log = RetrievalLog(
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
            query=query,
            chunks_retrieved=chunks_retrieved,
            chunks_after_filter=chunks_after_filter,
            chunks_after_dedup=chunks_after_dedup,
            chunks_after_rerank=chunks_after_rerank,
            top_chunk_score=top_chunk_score,
            avg_chunk_score=avg_chunk_score,
            min_chunk_score=min_chunk_score,
            chunk_details=chunk_details,
            cited_chunk_ids=cited_chunk_ids,
            query_embedding_time_ms=query_embedding_time_ms,
            retrieval_time_ms=retrieval_time_ms,
            rerank_time_ms=rerank_time_ms,
            total_time_ms=total_time_ms,
            llm_time_ms=llm_time_ms,
            answer_generated=answer_gen_int,
            answer_length=answer_length,
            error_message=error_message,
            # V2.0 质量保障字段
            confidence_score=confidence_score,
            faithfulness_score=faithfulness_score,
            has_hallucination=has_hallucination_int,
            retrieval_mode=retrieval_mode or "hybrid",
            refusal_reason=refusal_reason,
            refusal_message=refusal_message,
            citation_accuracy=citation_accuracy,
            latency_breakdown=latency_breakdown or {},
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_log(db: Session, log_id: int) -> RetrievalLog | None:
        """Get a retrieval log by ID."""
        stmt = select(RetrievalLog).where(RetrievalLog.id == log_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_logs(
        db: Session,
        knowledge_base_id: int | None = None,
        user_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        has_feedback: bool | None = None,
        feedback_type: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RetrievalLog], int]:
        """
        List retrieval logs with filters.
        Returns (logs, total_count).
        """
        conditions = []

        if knowledge_base_id is not None:
            conditions.append(RetrievalLog.knowledge_base_id == knowledge_base_id)
        if user_id is not None:
            conditions.append(RetrievalLog.user_id == user_id)
        if start_date is not None:
            conditions.append(RetrievalLog.created_at >= start_date)
        if end_date is not None:
            conditions.append(RetrievalLog.created_at <= end_date)
        if min_score is not None:
            conditions.append(RetrievalLog.top_chunk_score >= min_score)
        if max_score is not None:
            conditions.append(RetrievalLog.top_chunk_score <= max_score)

        # Build base query
        base_query = select(RetrievalLog)
        if conditions:
            base_query = base_query.where(and_(*conditions))

        # Filter by feedback
        if has_feedback is not None:
            if has_feedback:
                base_query = base_query.where(
                    RetrievalLog.id.in_(
                        select(RetrievalFeedback.retrieval_log_id).distinct()
                    )
                )
            else:
                base_query = base_query.where(
                    ~RetrievalLog.id.in_(
                        select(RetrievalFeedback.retrieval_log_id).distinct()
                    )
                )

        if feedback_type is not None:
            base_query = base_query.where(
                RetrievalLog.id.in_(
                    select(RetrievalFeedback.retrieval_log_id)
                    .where(RetrievalFeedback.feedback_type == feedback_type)
                    .distinct()
                )
            )

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = db.execute(count_query).scalar() or 0

        # Get paginated results
        stmt = base_query.order_by(desc(RetrievalLog.created_at)).offset(offset).limit(limit)
        logs = list(db.execute(stmt).scalars().all())

        return logs, total

    # ========== 用户反馈 ==========

    @staticmethod
    def add_feedback(
        db: Session,
        retrieval_log_id: int,
        user_id: int | None,
        feedback_type: str,
        rating: int | None = None,
        reason: str | None = None,
        comment: str | None = None,
        is_sample_marked: bool = False,
    ) -> tuple[RetrievalFeedback | None, str | None]:
        """Add feedback to a retrieval log. Supports V2.0 fields: rating and reason."""
        log = RetrievalLogService.get_log(db, retrieval_log_id)
        if log is None:
            return None, "检索日志不存在"

        if feedback_type not in [FeedbackType.HELPFUL.value, FeedbackType.NOT_HELPFUL.value]:
            return None, f"无效的反馈类型: {feedback_type}"
        
        # V2.0: 如果 rating 未提供，从 feedback_type 推导
        if rating is None:
            rating = 1 if feedback_type == FeedbackType.HELPFUL.value else -1

        feedback = RetrievalFeedback(
            retrieval_log_id=retrieval_log_id,
            user_id=user_id,
            feedback_type=feedback_type,
            rating=rating,  # 1 (thumbs_up) / -1 (thumbs_down)
            reason=reason,  # V2.0 用户输入原因
            comment=comment,
            is_sample_marked=1 if is_sample_marked else 0,  # 列类型为 Integer
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback, None

    @staticmethod
    def get_feedbacks_for_log(db: Session, retrieval_log_id: int) -> list[RetrievalFeedback]:
        """Get all feedbacks for a retrieval log."""
        stmt = (
            select(RetrievalFeedback)
            .where(RetrievalFeedback.retrieval_log_id == retrieval_log_id)
            .order_by(desc(RetrievalFeedback.created_at))
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def mark_as_sample(
        db: Session,
        feedback_id: int,
        is_sample: bool = True,
    ) -> tuple[RetrievalFeedback | None, str | None]:
        """Mark or unmark a feedback as problem sample."""
        stmt = select(RetrievalFeedback).where(RetrievalFeedback.id == feedback_id)
        feedback = db.execute(stmt).scalar_one_or_none()
        if feedback is None:
            return None, "反馈不存在"

        feedback.is_sample_marked = 1 if is_sample else 0  # 列类型为 Integer，存 1/0
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback, None

    @staticmethod
    def update_verification_metrics(
        db: Session,
        log_id: int,
        confidence_score: float | None = None,
        faithfulness_score: float | None = None,
        refusal_reason: str | None = None,
        refusal_message: str | None = None,
    ) -> tuple[bool, str | None]:
        """Update V2.0 verification metrics for a retrieval log."""
        stmt = select(RetrievalLog).where(RetrievalLog.id == log_id)
        log = db.execute(stmt).scalar_one_or_none()
        if not log:
            return False, "检索日志不存在"
        
        if confidence_score is not None:
            log.confidence_score = confidence_score
        if faithfulness_score is not None:
            log.faithfulness_score = faithfulness_score
        if refusal_reason is not None:
            log.refusal_reason = refusal_reason
        if refusal_message is not None:
            log.refusal_message = refusal_message
        
        db.commit()
        db.refresh(log)
        return True, None

    # ========== 统计分析 ==========

    @staticmethod
    def get_stats(
        db: Session,
        knowledge_base_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """
        Get retrieval statistics.
        Returns aggregated metrics for the dashboard.
        """
        conditions = []
        if knowledge_base_id is not None:
            conditions.append(RetrievalLog.knowledge_base_id == knowledge_base_id)
        if start_date is not None:
            conditions.append(RetrievalLog.created_at >= start_date)
        if end_date is not None:
            conditions.append(RetrievalLog.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        # Total queries
        total_queries = db.execute(
            select(func.count(RetrievalLog.id)).where(where_clause)
        ).scalar() or 0

        # Average scores
        avg_top_score = db.execute(
            select(func.avg(RetrievalLog.top_chunk_score)).where(where_clause)
        ).scalar()

        avg_chunks = db.execute(
            select(func.avg(RetrievalLog.chunks_after_rerank)).where(where_clause)
        ).scalar()

        avg_total_time = db.execute(
            select(func.avg(RetrievalLog.total_time_ms)).where(where_clause)
        ).scalar()

        # Feedback counts
        helpful_count = db.execute(
            select(func.count(RetrievalFeedback.id))
            .join(RetrievalLog, RetrievalFeedback.retrieval_log_id == RetrievalLog.id)
            .where(and_(where_clause, RetrievalFeedback.feedback_type == FeedbackType.HELPFUL.value))
        ).scalar() or 0

        not_helpful_count = db.execute(
            select(func.count(RetrievalFeedback.id))
            .join(RetrievalLog, RetrievalFeedback.retrieval_log_id == RetrievalLog.id)
            .where(and_(where_clause, RetrievalFeedback.feedback_type == FeedbackType.NOT_HELPFUL.value))
        ).scalar() or 0

        # Problem samples count
        sample_count = db.execute(
            select(func.count(RetrievalFeedback.id))
            .join(RetrievalLog, RetrievalFeedback.retrieval_log_id == RetrievalLog.id)
            .where(and_(where_clause, RetrievalFeedback.is_sample_marked == 1))
        ).scalar() or 0

        # Calculate not helpful ratio
        total_feedback = helpful_count + not_helpful_count
        not_helpful_ratio = (not_helpful_count / total_feedback * 100) if total_feedback > 0 else 0

        return {
            "total_queries": total_queries,
            "avg_top_score": float(round(avg_top_score, 4)) if avg_top_score is not None else None,
            "avg_chunks_returned": float(round(avg_chunks, 2)) if avg_chunks is not None else None,
            "avg_response_time_ms": float(round(avg_total_time, 2)) if avg_total_time is not None else None,
            "helpful_count": helpful_count,
            "not_helpful_count": not_helpful_count,
            "not_helpful_ratio": float(round(not_helpful_ratio, 2)),
            "sample_count": sample_count,
        }

    @staticmethod
    def get_stats_by_knowledge_base(
        db: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict]:
        """Get stats grouped by knowledge base."""
        conditions = []
        if start_date is not None:
            conditions.append(RetrievalLog.created_at >= start_date)
        if end_date is not None:
            conditions.append(RetrievalLog.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        stmt = (
            select(
                RetrievalLog.knowledge_base_id,
                func.count(RetrievalLog.id).label("query_count"),
                func.avg(RetrievalLog.top_chunk_score).label("avg_score"),
                func.avg(RetrievalLog.total_time_ms).label("avg_time"),
            )
            .where(where_clause)
            .group_by(RetrievalLog.knowledge_base_id)
            .order_by(desc(func.count(RetrievalLog.id)))
        )

        results = db.execute(stmt).all()
        return [
            {
                "knowledge_base_id": row.knowledge_base_id,
                "query_count": row.query_count,
                "avg_score": float(round(row.avg_score, 4)) if row.avg_score is not None else None,
                "avg_time_ms": float(round(row.avg_time, 2)) if row.avg_time is not None else None,
            }
            for row in results
        ]

    @staticmethod
    def get_stats_by_date(
        db: Session,
        knowledge_base_id: int | None = None,
        days: int = 7,
    ) -> list[dict]:
        """Get daily stats for the past N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        conditions = [RetrievalLog.created_at >= start_date]
        if knowledge_base_id is not None:
            conditions.append(RetrievalLog.knowledge_base_id == knowledge_base_id)

        stmt = (
            select(
                func.date(RetrievalLog.created_at).label("date"),
                func.count(RetrievalLog.id).label("query_count"),
                func.avg(RetrievalLog.top_chunk_score).label("avg_score"),
            )
            .where(and_(*conditions))
            .group_by(func.date(RetrievalLog.created_at))
            .order_by(func.date(RetrievalLog.created_at))
        )

        results = db.execute(stmt).all()
        return [
            {
                "date": str(row.date),
                "query_count": row.query_count,
                "avg_score": float(round(row.avg_score, 4)) if row.avg_score is not None else None,
            }
            for row in results
        ]
