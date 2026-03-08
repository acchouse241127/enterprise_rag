"""Knowledge base APIs."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_editor_user
from app.models.user import User
from app.schemas import KnowledgeBaseCreateRequest, KnowledgeBaseData, KnowledgeBaseUpdateRequest
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sort_by: str = "created_at",
    order: str = "desc",
) -> dict:
    """List all knowledge bases with document count. OPT-026: sort_by=created_at|name, order=asc|desc."""
    if sort_by not in ("created_at", "name"):
        sort_by = "created_at"
    if order not in ("asc", "desc"):
        order = "desc"
    items = KnowledgeBaseService.list_all_with_doc_count(db, sort_by=sort_by, order=order)
    data = []
    for item in items:
        kb_data = KnowledgeBaseData.model_validate(item["kb"]).model_dump(mode="json")
        kb_data["document_count"] = item["document_count"]
        data.append(kb_data)
    return {"code": 0, "message": "success", "data": data}


@router.post("")
def create_knowledge_base(
    payload: KnowledgeBaseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_editor_user),  # RBAC: 需要编辑者权限
) -> dict:
    """Create a knowledge base. Requires editor or admin role."""
    existing = KnowledgeBaseService.get_by_name(db, payload.name.strip())
    if existing is not None:
        return {"code": 1001, "message": "参数错误", "detail": "知识库名称已存在"}

    kb = KnowledgeBaseService.create(db, payload, created_by=current_user.id)
    return {
        "code": 0,
        "message": "success",
        "data": KnowledgeBaseData.model_validate(kb).model_dump(mode="json"),
    }


@router.get("/{knowledge_base_id}")
def get_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a knowledge base by id."""
    kb = KnowledgeBaseService.get_by_id(db, knowledge_base_id)
    if kb is None:
        return {"code": 4040, "message": "资源不存在", "detail": "知识库不存在"}
    return {
        "code": 0,
        "message": "success",
        "data": KnowledgeBaseData.model_validate(kb).model_dump(mode="json"),
    }


@router.put("/{knowledge_base_id}")
def update_knowledge_base(
    knowledge_base_id: int,
    payload: KnowledgeBaseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_editor_user),  # RBAC: 需要编辑者权限
) -> dict:
    """Update a knowledge base. Requires editor or admin role."""
    kb = KnowledgeBaseService.get_by_id(db, knowledge_base_id)
    if kb is None:
        return {"code": 4040, "message": "资源不存在", "detail": "知识库不存在"}

    if payload.name is not None:
        existing = KnowledgeBaseService.get_by_name(db, payload.name.strip())
        if existing is not None and existing.id != kb.id:
            return {"code": 1001, "message": "参数错误", "detail": "知识库名称已存在"}

    updated = KnowledgeBaseService.update(db, kb, payload)
    return {
        "code": 0,
        "message": "success",
        "data": KnowledgeBaseData.model_validate(updated).model_dump(mode="json"),
    }


@router.delete("/{knowledge_base_id}")
def delete_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_editor_user),  # RBAC: 需要编辑者权限
) -> dict:
    """Delete a knowledge base. Requires editor or admin role."""
    kb = KnowledgeBaseService.get_by_id(db, knowledge_base_id)
    if kb is None:
        return {"code": 4040, "message": "资源不存在", "detail": "知识库不存在"}

    ok, err = KnowledgeBaseService.delete(db, kb)
    if not ok and err:
        logger.warning("delete knowledge_base %s failed: %s", knowledge_base_id, err)
        raise HTTPException(status_code=500, detail=f"删除失败: {err}")
    return {"code": 0, "message": "success", "data": {"deleted": True}}


@router.get("/{knowledge_base_id}/documents")
def list_knowledge_base_documents(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all documents in a knowledge base."""
    kb = KnowledgeBaseService.get_by_id(db, knowledge_base_id)
    if kb is None:
        return {"code": 4040, "message": "资源不存在", "detail": "知识库不存在"}

    documents = KnowledgeBaseService.get_documents(db, knowledge_base_id)
    data = []
    for doc in documents:
        data.append({
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "status": doc.status,
            "parser_message": doc.parser_message,
            "version": doc.version,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        })
    return {"code": 0, "message": "success", "data": data}

