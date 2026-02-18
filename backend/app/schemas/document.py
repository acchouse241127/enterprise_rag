"""Document schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentData(BaseModel):
    """Document response model."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    knowledge_base_id: int
    title: str
    filename: str
    file_type: str
    file_size: int
    file_hash: str
    status: str
    parser_message: str | None
    version: int
    parent_document_id: int | None
    is_current: bool
    created_by: int | None
    source_url: str | None = None
    created_at: datetime
    updated_at: datetime

