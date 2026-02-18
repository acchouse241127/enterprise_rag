"""Question answering schemas."""

from typing import Any

from pydantic import BaseModel, Field


class QaAskRequest(BaseModel):
    """Ask request payload."""

    knowledge_base_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=64)
    history_turns: int | None = Field(default=None, ge=1, le=20)
    system_prompt_version: str | None = Field(default=None, max_length=8)


class QaAskData(BaseModel):
    """Ask response payload."""

    answer: str | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_count: int = 0
    llm_failed: bool = False
    error_message: str | None = None
    retrieved_chunks: list[dict[str, Any]] | None = None
    conversation_id: str | None = None
    retrieval_log_id: int | None = None  # Phase 3.2: for user feedback
