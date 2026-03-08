"""Chunk ORM model for BM25 full-text search and parent document retrieval.

Author: C2
Date: 2026-03-03
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Chunk(Base):
    """Document chunk for BM25 full-text search and parent document retrieval."""

    __tablename__ = "chunks"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=lambda: __import__("uuid").uuid4())
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    knowledge_base_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    collection_name: Mapped[str] = mapped_column(String(200), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_mode: Mapped[str | None] = mapped_column(String(30))
    token_count: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(500))
    parent_chunk_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("chunks.id"))
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
