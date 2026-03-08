"""
Conversation API endpoints for export and sharing.

Phase 3.3: 对话导出与分享
Author: C2
Date: 2026-02-14
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ============== Schemas ==============
class ConversationCreate(BaseModel):
    knowledge_base_id: int
    title: str | None = None


class MessageCreate(BaseModel):
    role: str  # user / assistant
    content: str
    extra_data: dict | None = None


class ShareSettings(BaseModel):
    expires_in_days: int | None = 7


class ConversationResponse(BaseModel):
    id: int
    conversation_id: str
    knowledge_base_id: int
    knowledge_base_name: str | None = None  # V2.0: 新增
    title: str | None
    message_count: int | None = None  # V2.0: 新增
    last_question: str | None = None  # V2.0: 新增
    is_shared: bool
    share_token: str | None
    share_expires_at: str | None
    user_id: int | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    extra_data: dict | None
    created_at: str

    class Config:
        from_attributes = True


# ============== Endpoints ==============
@router.post("", response_model=ConversationResponse)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation."""
    conv = ConversationService.create_conversation(
        db,
        knowledge_base_id=data.knowledge_base_id,
        user_id=current_user.id,
        title=data.title,
    )
    return ConversationResponse(
        id=conv.id,
        conversation_id=conv.conversation_id,
        knowledge_base_id=conv.knowledge_base_id,
        title=conv.title,
        is_shared=conv.is_shared,
        share_token=conv.share_token,
        share_expires_at=conv.share_expires_at.isoformat() if conv.share_expires_at else None,
        user_id=conv.user_id,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    knowledge_base_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's conversations."""
    conversations = ConversationService.list_conversations(
        db,
        user_id=current_user.id,
        knowledge_base_id=knowledge_base_id,
        limit=limit,
        offset=offset,
    )
    
    # 获取知识库名称映射
    from app.services.knowledge_base_service import KnowledgeBaseService
    kb_cache: dict[int, str] = {}
    
    result = []
    for c in conversations:
        # 获取知识库名称
        kb_name = None
        if c.knowledge_base_id not in kb_cache:
            kb = KnowledgeBaseService.get_by_id(db, c.knowledge_base_id)
            kb_cache[c.knowledge_base_id] = kb.name if kb else None
        kb_name = kb_cache.get(c.knowledge_base_id)
        
        # 获取消息数量
        message_count = len(ConversationService.get_messages(db, c.id))
        
        # 获取最后一条用户消息作为 last_question
        messages = ConversationService.get_messages(db, c.id)
        last_question = None
        for msg in reversed(messages):
            if msg.role == "user":
                last_question = msg.content[:100] if msg.content else None
                break
        
        result.append(ConversationResponse(
            id=c.id,
            conversation_id=c.conversation_id,
            knowledge_base_id=c.knowledge_base_id,
            title=c.title,
            is_shared=c.is_shared,
            share_token=c.share_token,
            share_expires_at=c.share_expires_at.isoformat() if c.share_expires_at else None,
            user_id=c.user_id,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        ))
    
    return result


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversation details."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此对话")

    return ConversationResponse(
        id=conv.id,
        conversation_id=conv.conversation_id,
        knowledge_base_id=conv.knowledge_base_id,
        title=conv.title,
        is_shared=conv.is_shared,
        share_token=conv.share_token,
        share_expires_at=conv.share_expires_at.isoformat() if conv.share_expires_at else None,
        user_id=conv.user_id,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def add_message(
    conversation_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a message to a conversation."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此对话")

    msg = ConversationService.add_message(
        db,
        conversation_id=conversation_id,
        role=data.role,
        content=data.content,
        extra_data=data.extra_data,
    )
    return MessageResponse(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        extra_data=msg.extra_data,
        created_at=msg.created_at.isoformat(),
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all messages in a conversation."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此对话")

    messages = ConversationService.get_messages(db, conversation_id)
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            extra_data=m.extra_data,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.post("/{conversation_id}/share")
def enable_sharing(
    conversation_id: int,
    settings: ShareSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable sharing for a conversation."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作此对话")

    conv, token = ConversationService.enable_sharing(
        db, conversation_id, expires_in_days=settings.expires_in_days
    )
    return {
        "share_token": token,
        "share_url": f"/share/{token}",
        "expires_at": conv.share_expires_at.isoformat() if conv.share_expires_at else None,
    }


@router.delete("/{conversation_id}/share")
def disable_sharing(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disable sharing for a conversation."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作此对话")

    ConversationService.disable_sharing(db, conversation_id)
    return {"message": "分享已关闭"}


@router.get("/{conversation_id}/export/markdown")
def export_markdown(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export conversation to Markdown."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此对话")

    md_content = ConversationService.export_to_markdown(db, conversation_id)
    if not md_content:
        raise HTTPException(status_code=500, detail="导出失败")

    filename = f"conversation_{conv.conversation_id[:8]}.md"
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{conversation_id}/export/pdf")
def export_pdf(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export conversation to PDF."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此对话")

    pdf_bytes = ConversationService.export_to_pdf_bytes(db, conversation_id)
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="导出失败")

    filename = f"conversation_{conv.conversation_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{conversation_id}/export/docx")
def export_docx(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Export conversation to DOCX."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此对话")
    docx_bytes = ConversationService.export_to_docx_bytes(db, conversation_id)
    if not docx_bytes:
        raise HTTPException(status_code=500, detail="导出失败")
    filename = f"conversation_{conv.conversation_id[:8]}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation."""
    conv = ConversationService.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除此对话")

    ConversationService.delete_conversation(db, conversation_id)
    return {"message": "对话已删除"}


# ============== Public Share Endpoint ==============
@router.get("/share/{share_token}")
def get_shared_conversation(
    share_token: str,
    db: Session = Depends(get_db),
):
    """Get a shared conversation (no auth required)."""
    conv = ConversationService.get_by_share_token(db, share_token)
    if not conv:
        raise HTTPException(status_code=404, detail="分享链接无效或已过期")

    messages = ConversationService.get_messages(db, conv.id)
    
    # 获取知识库名称
    from app.services.knowledge_base_service import KnowledgeBaseService
    kb = KnowledgeBaseService.get_by_id(db, conv.knowledge_base_id)
    kb_name = kb.name if kb else None
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": str(conv.conversation_id),
            "title": conv.title,
            "knowledge_base_name": kb_name,
            "created_at": conv.created_at.isoformat(),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        },
    }
