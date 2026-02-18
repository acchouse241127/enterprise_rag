"""
Async task model for background job tracking.

Phase 3.3: 异步任务队列
Author: C2
Date: 2026-02-14
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TaskStatus(str, Enum):
    """Task status enum."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task type enum."""
    DOCUMENT_PARSE = "document_parse"
    DOCUMENT_VECTORIZE = "document_vectorize"
    FOLDER_SYNC = "folder_sync"
    EXPORT_CONVERSATION = "export_conversation"


class AsyncTask(Base):
    """
    Async task tracking for background jobs.
    Used for large file parsing, folder sync, exports, etc.
    """

    __tablename__ = "async_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=TaskStatus.PENDING.value, index=True)
    
    # Related entity (e.g., document_id, knowledge_base_id)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    # Progress tracking
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0-100
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Task input/output
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    
    # User tracking
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now()
    )
