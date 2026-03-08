"""PII anonymization rule model.

Author: C2
Date: 2026-03-03
"""

from datetime import datetime

from sqlalchemy import Boolean, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PiiRule(Base):
    """PII anonymization rule for detecting and masking sensitive data."""

    __tablename__ = "pii_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    mask_format: Mapped[str] = mapped_column(String(100), default="****")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PiiRule(id={self.id}, name={self.name})>"
