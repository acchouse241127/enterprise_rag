"""Question answering schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class QueryExpansionLlmConfig(BaseModel):
    """Request-level LLM config for query expansion."""

    provider: Literal["openai", "deepseek"] | None = Field(default=None)
    model_name: str | None = Field(default=None, max_length=128)
    base_url: str | None = Field(default=None, max_length=500)
    api_key: str | None = Field(default=None, max_length=500)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    timeout_seconds: int | None = Field(default=None, ge=1, le=600)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    retry_base_delay: float | None = Field(default=None, ge=0.0, le=60.0)


class QaAskRequest(BaseModel):
    """Ask request payload."""

    knowledge_base_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=64)
    history_turns: int | None = Field(default=None, ge=1, le=20)
    system_prompt_version: str | None = Field(default=None, max_length=8)
    strategy: str | None = Field(
        default=None,
        description="Retrieval strategy: smart (recommended), precise (accurate), fast (speed), deep (comprehensive)",
    )
    # V2.0: 检索模式
    retrieval_mode: Literal["vector", "bm25", "hybrid"] | None = Field(
        default=None,
        description="Retrieval mode: vector (dense), bm25 (sparse), hybrid",
    )
    query_expansion_mode: Literal["rule", "llm", "hybrid"] | None = Field(
        default=None,
        description="Request-level query expansion mode",
    )
    query_expansion_target: Literal["cloud", "local", "default"] | None = Field(
        default=None,
        description="Request-level query expansion target provider group",
    )
    query_expansion_llm: QueryExpansionLlmConfig | None = Field(
        default=None,
        description="Request-level query expansion LLM config",
    )


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
