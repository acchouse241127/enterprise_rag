"""Knowledge base schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreateRequest(BaseModel):
    """Create knowledge base payload."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    created_by: int | None = None
    # V2.0 新增字段
    chunk_size: int | None = Field(default=None, ge=100, le=10000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=2000)
    chunk_mode: Literal["char", "sentence", "token", "chinese_recursive"] | None = Field(default=None)
    parent_retrieval_mode: Literal["physical", "dynamic", "off"] | None = Field(default=None)
    dynamic_expand_n: int | None = Field(default=None, ge=1, le=10)
    # V2.0: 默认检索策略
    default_retrieval_strategy: Literal["smart", "precise", "fast", "deep"] | None = Field(default=None)


class KnowledgeBaseUpdateRequest(BaseModel):
    """Update knowledge base payload."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    # V2.0 新增字段
    chunk_size: int | None = Field(default=None, ge=100, le=10000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=2000)
    chunk_mode: Literal["char", "sentence", "token", "chinese_recursive"] | None = Field(default=None)
    parent_retrieval_mode: Literal["physical", "dynamic", "off"] | None = Field(default=None)
    dynamic_expand_n: int | None = Field(default=None, ge=1, le=10)
    # V2.0: 默认检索策略
    default_retrieval_strategy: Literal["smart", "precise", "fast", "deep"] | None = Field(default=None)


class KnowledgeBaseData(BaseModel):
    """Knowledge base response model."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    # V2.0 新增字段
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    chunk_mode: str | None = None
    parent_retrieval_mode: str | None = None
    dynamic_expand_n: int | None = None
    # V2.0: 默认检索策略
    default_retrieval_strategy: str | None = None

