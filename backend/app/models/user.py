"""
User model definition.

Author: C2
Date: 2026-02-13
Updated: 2026-02-13 (Phase 2.3 RBAC)
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoleEnum(str, Enum):
    """User role enumeration for RBAC."""

    ADMIN = "admin"  # 管理员：全部权限
    EDITOR = "editor"  # 编辑者：可管理知识库和文档
    VIEWER = "viewer"  # 查看者：仅可问答和查看


class User(Base):
    """System user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=RoleEnum.VIEWER.value)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # ToB 多租户预留
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # 用户-知识库权限关联
    kb_permissions: Mapped[list["UserKnowledgeBasePermission"]] = relationship(
        "UserKnowledgeBasePermission", back_populates="user", cascade="all, delete-orphan"
    )

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission based on role."""
        permissions_map = {
            RoleEnum.ADMIN.value: {"admin", "edit", "view", "delete", "create"},
            RoleEnum.EDITOR.value: {"edit", "view", "create"},
            RoleEnum.VIEWER.value: {"view"},
        }
        return permission in permissions_map.get(self.role, set())


class UserKnowledgeBasePermission(Base):
    """User-KnowledgeBase permission mapping for fine-grained access control."""

    __tablename__ = "user_kb_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge_base_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(20), nullable=False, default="view")  # view, edit, admin
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="kb_permissions")
    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="user_permissions")


# Import KnowledgeBase for type hints (avoid circular import at runtime)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase

