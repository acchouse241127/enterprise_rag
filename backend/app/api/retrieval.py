"""
Retrieval log and feedback APIs.

Phase 3.2: 检索质量看板
Author: C2
Date: 2026-02-13
"""

from datetime import datetime, time

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.models.user import User
from app.services.retrieval_log_service import RetrievalLogService

router = APIRouter()


class FeedbackCreate(BaseModel):
    """Request body for adding feedback."""
    retrieval_log_id: int
    feedback_type: str  # helpful / not_helpful
    comment: str | None = None


class MarkSampleRequest(BaseModel):
    """Request body for marking sample."""
    is_sample: bool = True


# ========== 检索日志 ==========


@router.get("/retrieval/logs")
def list_retrieval_logs(
    knowledge_base_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    has_feedback: bool | None = None,
    feedback_type: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    List retrieval logs with filters.
    Supports filtering by knowledge_base, date range, feedback status, and score range.
    """
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = None
    if end_date:
        end_dt = datetime.fromisoformat(end_date) if "T" in end_date else datetime.combine(
            datetime.fromisoformat(end_date).date(), time.max
        )

    logs, total = RetrievalLogService.list_logs(
        db=db,
        knowledge_base_id=knowledge_base_id,
        start_date=start_dt,
        end_date=end_dt,
        has_feedback=has_feedback,
        feedback_type=feedback_type,
        min_score=min_score,
        max_score=max_score,
        limit=limit,
        offset=offset,
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": total,
            "items": [
                {
                    "id": log.id,
                    "knowledge_base_id": log.knowledge_base_id,
                    "user_id": log.user_id,
                    "query": log.query,
                    "chunks_retrieved": log.chunks_retrieved,
                    "chunks_after_rerank": log.chunks_after_rerank,
                    "top_chunk_score": log.top_chunk_score,
                    "avg_chunk_score": log.avg_chunk_score,
                    "total_time_ms": log.total_time_ms,
                    "answer_generated": log.answer_generated,
                    "created_at": log.created_at.isoformat(),
                    "feedbacks": [
                        {
                            "id": fb.id,
                            "feedback_type": fb.feedback_type,
                            "is_sample_marked": fb.is_sample_marked,
                        }
                        for fb in log.feedbacks
                    ],
                }
                for log in logs
            ],
        },
    }


@router.get("/retrieval/logs/{log_id}")
def get_retrieval_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a single retrieval log with full details."""
    log = RetrievalLogService.get_log(db, log_id)
    if log is None:
        return {"code": 4040, "message": "资源不存在", "detail": "检索日志不存在"}

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": log.id,
            "knowledge_base_id": log.knowledge_base_id,
            "user_id": log.user_id,
            "query": log.query,
            "query_embedding_time_ms": log.query_embedding_time_ms,
            "retrieval_time_ms": log.retrieval_time_ms,
            "rerank_time_ms": log.rerank_time_ms,
            "total_time_ms": log.total_time_ms,
            "llm_time_ms": log.llm_time_ms,
            "chunks_retrieved": log.chunks_retrieved,
            "chunks_after_filter": log.chunks_after_filter,
            "chunks_after_dedup": log.chunks_after_dedup,
            "chunks_after_rerank": log.chunks_after_rerank,
            "top_chunk_score": log.top_chunk_score,
            "avg_chunk_score": log.avg_chunk_score,
            "min_chunk_score": log.min_chunk_score,
            "chunk_details": log.chunk_details,
            "answer_generated": log.answer_generated,
            "answer_length": log.answer_length,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat(),
            "feedbacks": [
                {
                    "id": fb.id,
                    "user_id": fb.user_id,
                    "feedback_type": fb.feedback_type,
                    "comment": fb.comment,
                    "is_sample_marked": fb.is_sample_marked,
                    "created_at": fb.created_at.isoformat(),
                }
                for fb in log.feedbacks
            ],
        },
    }


# ========== 用户反馈 ==========


@router.post("/retrieval/feedback")
def add_feedback(
    body: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Add feedback to a retrieval log."""
    feedback, err = RetrievalLogService.add_feedback(
        db=db,
        retrieval_log_id=body.retrieval_log_id,
        user_id=current_user.id,
        feedback_type=body.feedback_type,
        comment=body.comment,
    )
    if err:
        return {"code": 4001, "message": "添加反馈失败", "detail": err}

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": feedback.id,
            "retrieval_log_id": feedback.retrieval_log_id,
            "feedback_type": feedback.feedback_type,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat(),
        },
    }


@router.post("/retrieval/feedback/{feedback_id}/mark-sample")
def mark_feedback_as_sample(
    feedback_id: int,
    body: MarkSampleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Mark or unmark a feedback as problem sample."""
    feedback, err = RetrievalLogService.mark_as_sample(db, feedback_id, body.is_sample)
    if err:
        return {"code": 4001, "message": "标记失败", "detail": err}

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": feedback.id,
            "is_sample_marked": feedback.is_sample_marked,
        },
    }


# ========== 统计分析 ==========


@router.get("/retrieval/stats")
def get_retrieval_stats(
    knowledge_base_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get retrieval statistics."""
    # OPT-027: 日期解析，end_date 取当日 23:59:59 以包含当天数据
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = None
    if end_date:
        end_dt = datetime.fromisoformat(end_date) if "T" in end_date else datetime.combine(
            datetime.fromisoformat(end_date).date(), time.max
        )

    stats = RetrievalLogService.get_stats(
        db=db,
        knowledge_base_id=knowledge_base_id,
        start_date=start_dt,
        end_date=end_dt,
    )
    # 看板无数据时前端可据此提示：检索日志是否已启用
    stats["retrieval_log_enabled"] = settings.retrieval_log_enabled

    return {"code": 0, "message": "success", "data": stats}


@router.get("/retrieval/stats/by-knowledge-base")
def get_stats_by_knowledge_base(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get statistics grouped by knowledge base."""
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = None
    if end_date:
        end_dt = datetime.fromisoformat(end_date) if "T" in end_date else datetime.combine(
            datetime.fromisoformat(end_date).date(), time.max
        )

    stats = RetrievalLogService.get_stats_by_knowledge_base(
        db=db,
        start_date=start_dt,
        end_date=end_dt,
    )

    return {"code": 0, "message": "success", "data": stats}


@router.get("/retrieval/stats/by-date")
def get_stats_by_date(
    knowledge_base_id: int | None = None,
    days: int = Query(default=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get daily statistics for the past N days."""
    stats = RetrievalLogService.get_stats_by_date(
        db=db,
        knowledge_base_id=knowledge_base_id,
        days=days,
    )

    return {"code": 0, "message": "success", "data": stats}


# ========== 问题样本 ==========


@router.get("/retrieval/samples")
def list_problem_samples(
    knowledge_base_id: int | None = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List retrieval logs marked as problem samples."""
    # Get logs with sample-marked feedbacks
    logs, total = RetrievalLogService.list_logs(
        db=db,
        knowledge_base_id=knowledge_base_id,
        limit=limit,
        offset=offset,
    )

    # Filter to only those with sample marks
    sample_logs = [
        log for log in logs
        if any(fb.is_sample_marked for fb in log.feedbacks)
    ]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": len(sample_logs),
            "items": [
                {
                    "id": log.id,
                    "knowledge_base_id": log.knowledge_base_id,
                    "query": log.query,
                    "top_chunk_score": log.top_chunk_score,
                    "created_at": log.created_at.isoformat(),
                    "feedbacks": [
                        {
                            "id": fb.id,
                            "feedback_type": fb.feedback_type,
                            "comment": fb.comment,
                            "is_sample_marked": fb.is_sample_marked,
                        }
                        for fb in log.feedbacks if fb.is_sample_marked
                    ],
                }
                for log in sample_logs
            ],
        },
    }
