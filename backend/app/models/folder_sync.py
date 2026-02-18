"""
Folder sync configuration model.

Phase 3.2: 文件夹同步配置
Author: C2
Date: 2026-02-13
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SyncStatus(str, Enum):
    """Sync job status."""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class FolderSyncConfig(Base):
    """Folder sync configuration for a knowledge base."""

    __tablename__ = "folder_sync_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    knowledge_base_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    directory_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    file_patterns: Mapped[str] = mapped_column(
        String(500), nullable=False, default="*.txt,*.md,*.pdf,*.docx,*.xlsx,*.pptx,*.png,*.jpg,*.jpeg"
    )  # 逗号分隔的文件模式（与文档上传格式一致）
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    last_sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default=SyncStatus.IDLE.value)
    last_sync_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_files_added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_sync_files_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_sync_files_deleted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    knowledge_base = relationship("KnowledgeBase", back_populates="folder_sync_config")


class FolderSyncLog(Base):
    """Log of folder sync operations."""

    __tablename__ = "folder_sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    folder_sync_config_id: Mapped[int] = mapped_column(
        ForeignKey("folder_sync_configs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    files_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_deleted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Integer, nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(20), nullable=False, default="poll")  # poll / manual
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
