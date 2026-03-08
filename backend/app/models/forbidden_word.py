"""Forbidden word model for content filtering.

Author: C2
Date: 2026-03-03
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ForbiddenWord(Base):
    """Forbidden word for content filtering and replacement."""

    __tablename__ = "forbidden_words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # absolute, misleading, etc.
    replacement: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    knowledge_base_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ForbiddenWord(id={self.id}, word={self.word}, category={self.category})>"
