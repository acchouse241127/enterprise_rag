"""Knowledge base schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreateRequest(BaseModel):
    """Create knowledge base payload."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    created_by: int | None = None


class KnowledgeBaseUpdateRequest(BaseModel):
    """Update knowledge base payload."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class KnowledgeBaseData(BaseModel):
    """Knowledge base response model."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

