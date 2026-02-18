"""
Knowledge base editing API endpoints.

Phase 3.3: 知识库在线编辑与分块调整
Author: C2
Date: 2026-02-14
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User
from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

router = APIRouter(prefix="/knowledge-bases", tags=["kb-edit"])


# ============== Schemas ==============
class DocumentContentUpdate(BaseModel):
    content: str


class ChunkSettingsUpdate(BaseModel):
    chunk_size: int | None = None
    chunk_overlap: int | None = None


class RechunkRequest(BaseModel):
    chunk_size: int | None = None
    chunk_overlap: int | None = None


class ChunkSettingsResponse(BaseModel):
    knowledge_base_id: int
    chunk_size: int
    chunk_overlap: int
    is_custom: bool
    global_defaults: dict


# ============== Document Content Editing ==============
@router.get("/documents/{document_id}/content")
def get_document_content(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document content for editing."""
    doc, error = KnowledgeBaseEditService.get_document_content(db, document_id)
    if error:
        raise HTTPException(status_code=404, detail=error)

    return {
        "id": doc.id,
        "title": doc.title,
        "filename": doc.filename,
        "content": doc.content_text or "",
        "status": doc.status,
        "parser_message": doc.parser_message,
    }


@router.put("/documents/{document_id}/content")
def update_document_content(
    document_id: int,
    data: DocumentContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update document content and re-vectorize."""
    doc, error = KnowledgeBaseEditService.update_document_content(
        db, document_id, data.content, updated_by=current_user.id
    )
    if error:
        raise HTTPException(status_code=400, detail=error)

    return {
        "id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "parser_message": doc.parser_message,
        "message": "文档内容已更新并重新向量化",
    }


# ============== Chunk Settings ==============
@router.get("/{knowledge_base_id}/chunk-settings", response_model=ChunkSettingsResponse)
def get_chunk_settings(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chunk settings for a knowledge base."""
    settings = KnowledgeBaseEditService.get_kb_chunk_settings(db, knowledge_base_id)
    if not settings:
        raise HTTPException(status_code=404, detail="知识库不存在")

    return ChunkSettingsResponse(**settings)


@router.put("/{knowledge_base_id}/chunk-settings", response_model=ChunkSettingsResponse)
def update_chunk_settings(
    knowledge_base_id: int,
    data: ChunkSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update chunk settings for a knowledge base."""
    kb, error = KnowledgeBaseEditService.update_kb_chunk_settings(
        db, knowledge_base_id, chunk_size=data.chunk_size, chunk_overlap=data.chunk_overlap
    )
    if error:
        raise HTTPException(status_code=400, detail=error)

    settings = KnowledgeBaseEditService.get_kb_chunk_settings(db, knowledge_base_id)
    return ChunkSettingsResponse(**settings)


# ============== Re-chunking ==============
@router.post("/documents/{document_id}/rechunk")
def rechunk_document(
    document_id: int,
    data: RechunkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-chunk a single document with optional custom parameters."""
    doc, chunk_count, error = KnowledgeBaseEditService.rechunk_document(
        db, document_id, chunk_size=data.chunk_size, chunk_overlap=data.chunk_overlap
    )
    if error:
        raise HTTPException(status_code=400, detail=error)

    return {
        "id": doc.id,
        "title": doc.title,
        "chunk_count": chunk_count,
        "parser_message": doc.parser_message,
        "message": f"文档已重新分块，共 {chunk_count} 个块",
    }


@router.post("/{knowledge_base_id}/rechunk-all")
def rechunk_all_documents(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-chunk all documents in a knowledge base using KB's chunk settings."""
    success_count, failed_count, error = KnowledgeBaseEditService.rechunk_all_documents(
        db, knowledge_base_id
    )
    if error:
        raise HTTPException(status_code=400, detail=error)

    return {
        "knowledge_base_id": knowledge_base_id,
        "success_count": success_count,
        "failed_count": failed_count,
        "message": f"重新分块完成：成功 {success_count} 个，失败 {failed_count} 个",
    }
