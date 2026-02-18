"""Question answering APIs."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas import QaAskData, QaAskRequest
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.qa_service import QaService

router = APIRouter()


def _enrich_chunks_with_filename(db: Session, chunks: list[dict]) -> list[dict]:
    """Add filename to each chunk from document_id."""
    result = []
    for c in chunks:
        meta = c.get("metadata") or {}
        doc_id = meta.get("document_id")
        filename = "未知文件"
        if doc_id is not None:
            doc = DocumentService.get_by_id(db, int(doc_id))
            if doc:
                filename = doc.filename
        result.append({
            "content": c.get("content", ""),
            "document_id": doc_id,
            "filename": filename,
            "chunk_index": meta.get("chunk_index"),
            "content_preview": (c.get("content") or "")[:300],
        })
    return result


@router.post("/qa/ask")
def ask_question(
    payload: QaAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Ask question and return answer with citations. On LLM failure returns retrieved chunks with filename."""
    data, err = QaService.ask(
        knowledge_base_id=payload.knowledge_base_id,
        question=payload.question,
        top_k=payload.top_k,
        conversation_id=payload.conversation_id,
        history_turns=payload.history_turns,
        user_id=current_user.id,  # Phase 3.2: for retrieval logging
        system_prompt_version=payload.system_prompt_version,
    )
    if err is not None:
        return {"code": 4001, "message": "请求失败", "detail": err}
    assert data is not None

    if data.get("llm_failed") and data.get("chunks"):
        data["retrieved_chunks"] = _enrich_chunks_with_filename(db, data["chunks"])
        del data["chunks"]

    # OPT-024: RAG 问答与对话管理打通，成功回答后持久化到 conversations
    answer_text = data.get("answer") or ""
    if answer_text and payload.conversation_id:
        try:
            ConversationService.persist_qa_turn(
                db,
                conversation_id_str=payload.conversation_id,
                knowledge_base_id=payload.knowledge_base_id,
                user_id=current_user.id,
                question=payload.question,
                answer=answer_text,
            )
        except Exception:
            pass  # 持久化失败不影响问答响应

    return {
        "code": 0,
        "message": "success",
        "data": QaAskData.model_validate(data).model_dump(mode="json"),
    }


@router.post("/qa/stream")
def stream_question(
    payload: QaAskRequest,
    current_user: User = Depends(get_current_user),
):
    """Ask question and stream answer chunks by SSE."""
    stream = QaService.stream_ask(
        knowledge_base_id=payload.knowledge_base_id,
        question=payload.question,
        top_k=payload.top_k,
        conversation_id=payload.conversation_id,
        history_turns=payload.history_turns,
        user_id=current_user.id,  # Phase 3.2: for retrieval logging
        system_prompt_version=payload.system_prompt_version,
    )
    return StreamingResponse(stream, media_type="text/event-stream")
