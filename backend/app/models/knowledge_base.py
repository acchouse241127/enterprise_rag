"""
Knowledge base model definition.

Author: C2
Date: 2026-02-13
Updated: 2026-02-14 (Phase 2.3 RBAC, Phase 3.2 Folder Sync, Phase 3.3 Chunk Settings)
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import UserKnowledgeBasePermission
    from app.models.folder_sync import FolderSyncConfig


class KnowledgeBase(Base):
    """Knowledge base metadata."""

    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Phase 3.3: 分块参数（可调）
    chunk_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 覆盖全局默认
    chunk_overlap: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # RBAC: 用户权限关联
    user_permissions: Mapped[list["UserKnowledgeBasePermission"]] = relationship(
        "UserKnowledgeBasePermission", back_populates="knowledge_base", cascade="all, delete-orphan"
    )

    # Phase 3.2: 文件夹同步配置
    folder_sync_config: Mapped["FolderSyncConfig | None"] = relationship(
        "FolderSyncConfig", back_populates="knowledge_base", uselist=False, cascade="all, delete-orphan"
    )

