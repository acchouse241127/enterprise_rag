"""
Conversation model for storing and exporting chat history.

Phase 3.3: 对话导出与分享
Author: C2
Date: 2026-02-14
"""

from datetime import datetime
import secrets

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Conversation(Base):
    """
    Stored conversation for export and sharing.
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    knowledge_base_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Share settings
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    share_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    
    # User tracking
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

    @staticmethod
    def generate_share_token() -> str:
        """Generate a secure share token."""
        return secrets.token_urlsafe(32)


class ConversationMessage(Base):
    """
    Individual message in a conversation.
    """

    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user / assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Extra data (citations, retrieval_log_id, etc.)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )

    # Relationship
    conversation = relationship("Conversation", back_populates="messages")
