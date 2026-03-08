"""SPLADE sparse embedding model.

Author: C2
Date: 2026-03-03
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SpladeEmbedding(Base):
    """SPLADE sparse embedding storage for chunks."""

    __tablename__ = "splade_embeddings"

    chunk_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), primary_key=True
    )
    sparse_vector: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<SpladeEmbedding(chunk_id={self.chunk_id})>"
