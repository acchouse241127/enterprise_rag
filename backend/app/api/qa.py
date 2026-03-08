"""Question answering APIs."""

import json
import logging

from typing import Any

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.models.user import User
from app.rag.retrieval_strategy import list_strategies
from app.schemas import QaAskData, QaAskRequest
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.qa_service import QaService

router = APIRouter()


@router.get("/qa/strategies")
def get_strategies():
    """List all available retrieval strategies."""
    return {"code": 0, "message": "success", "data": list_strategies()}


@router.get("/qa/expansion-meta")
def get_query_expansion_meta():
    """Query expansion metadata for frontend rendering."""
    overrides = getattr(settings, "llm_task_overrides", None) or {}
    query_override = overrides.get("query_expansion") if isinstance(overrides, dict) else None
    default_cloud_model_name = (
        query_override.get("model_name")
        if isinstance(query_override, dict) and query_override.get("model_name")
        else settings.llm_model_name
    )

    allowed_providers = {"deepseek", "openai"}
    configured_provider = (settings.llm_provider or "").lower()
    providers = sorted(allowed_providers | ({configured_provider} if configured_provider in allowed_providers else set()))
    return {
        "code": 0,
        "message": "success",
        "data": {
            "default_mode": settings.retrieval_query_expansion_mode,
            "default_cloud_model_name": default_cloud_model_name,
            "local_available": False,
            "supported_modes": ["rule", "llm", "hybrid"],
            "supported_targets": ["cloud", "local", "default"],
            "providers": providers,
        },
    }


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


def _enrich_citations_with_filename(db: Session, citations: list[dict]) -> list[dict]:
    """Add filename to each citation from document_id."""
    result = []
    for c in citations:
        doc_id = c.get("document_id")
        filename = c.get("filename") or "未知文件"
        if doc_id is not None:
            doc = DocumentService.get_by_id(db, int(doc_id))
            if doc:
                filename = doc.filename
        result.append({**c, "filename": filename})
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
        strategy=payload.strategy,  # B4.4: retrieval strategy
        retrieval_mode=payload.retrieval_mode,  # V2.0: retrieval mode
        query_expansion_mode=payload.query_expansion_mode,
        query_expansion_target=payload.query_expansion_target,
        query_expansion_llm=(
            payload.query_expansion_llm.model_dump(exclude_none=True)
            if payload.query_expansion_llm
            else None
        ),
    )
    if err is not None:
        return {"code": 4001, "message": "请求失败", "detail": err}
    assert data is not None

    if data.get("llm_failed") and data.get("chunks"):
        data["retrieved_chunks"] = _enrich_chunks_with_filename(db, data["chunks"])
        del data["chunks"]
    elif data.get("citations"):
        data["citations"] = _enrich_citations_with_filename(db, data["citations"])

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
        except Exception as e:
            logger.debug("Failed to persist QA turn: %s", e)  # 持久化失败不影响问答响应

    return {
        "code": 0,
        "message": "success",
        "data": QaAskData.model_validate(data).model_dump(mode="json"),
    }


def _stream_with_enriched_citations(stream, db: Session):
    """Wrap stream to enrich citations with filename before yielding."""
    for chunk in stream:
        if isinstance(chunk, str) and '"type": "citations"' in chunk:
            try:
                start = chunk.find("data: ") + 6
                data = json.loads(chunk[start:].strip())
                if data.get("type") == "citations" and data.get("data"):
                    data["data"] = _enrich_citations_with_filename(db, data["data"])
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    continue
            except Exception as e:
                logger.warning("Failed to enrich citations in stream: %s", e)
        yield chunk


@router.post("/qa/stream")
def stream_question(
    payload: QaAskRequest,
    db: Session = Depends(get_db),
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
        strategy=payload.strategy,  # B4.4: retrieval strategy
        retrieval_mode=payload.retrieval_mode,  # V2.0: retrieval mode
        query_expansion_mode=payload.query_expansion_mode,
        query_expansion_target=payload.query_expansion_target,
        query_expansion_llm=(
            payload.query_expansion_llm.model_dump(exclude_none=True)
            if payload.query_expansion_llm
            else None
        ),
    )
    return StreamingResponse(_stream_with_enriched_citations(stream, db), media_type="text/event-stream")
@router.get("/qa/vlm/config")
def get_vlm_config() -> dict[str, Any]:
    """Get VLM configuration for frontend.

    Returns:
        VLM configuration status and settings
    """
    return {
        "code": 0,
        "message": "success",
        "data": {
            "enabled": settings.vlm_enabled,
            "provider": settings.vlm_provider,
            "model_name": settings.vlm_model_name,
            "available": settings.vlm_enabled and bool(settings.vlm_api_key or settings.llm_api_key),
        },
    }


