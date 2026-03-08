"""Enhanced Question Answering APIs with modality awareness and VLM support.

Author: C2
Date: 2026-03-07
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.services.enhanced_retrieval_service import EnhancedRetrievalService
from app.schemas import QaAskData, QaAskRequest

from app.services.qa_service import QaService
from app.rag.prompts import get_system_prompt


logger = logging.getLogger(__name__)

router = APIRouter()


def get_enhanced_retrieval_service() -> EnhancedRetrievalService:
    """Get enhanced retrieval service instance (singleton pattern)."""
    return EnhancedRetrievalService()


@router.get("/qa/enhanced/strategies")
def get_strategies():
    """Get available enhanced retrieval strategies."""
    strategies = []

    if settings.modality_aware_ranking_enabled:
        strategies.append("modality-aware")

    return {"code": 0, "message": "success", "data": strategies}


@router.get("/qa/enhanced")
def enhanced_ask(
    payload: QaAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service: EnhancedRetrievalService = Depends(get_enhanced_retrieval_service),
):
    """Enhanced question answering with modality awareness.

    Args:
        payload: Question ask request
        db: Database session
        current_user: Current authenticated user
        service: Enhanced retrieval service

    Returns:
        Response with enhanced answer and metadata
    """
    try:
        # Step 1: Retrieve with modality awareness
        retrieved_chunks, metadata = service.retrieve_with_modality_aware(
            query=payload.question,
            knowledge_base_id=payload.knowledge_base_id,
            top_k=payload.top_k or 5,
        )

        # Step 2: Generate answer
        answer_data = QaService.ask(
            db=db,
            current_user=current_user,
            knowledge_base_id=payload.knowledge_base_id,
            question=payload.question,
            retrieved_chunks=retrieved_chunks,
            conversation_id=payload.conversation_id,
            history_turns=payload.history_turns,
            system_prompt_version=payload.system_prompt_version,
            strategy="enhanced",
        )

        # Get enhancement info for frontend
        enhancement_info = service.get_enhancement_info(payload.question)

        logger.info(f"Enhanced QA request for KB {payload.knowledge_base_id}")

        return {
            "code": 0,
            "message": "success",
            "data": QaAskData.model_validate(answer_data),
            "enhancement": enhancement_info,
        }

    except Exception as e:
        logger.error(f"Enhanced QA request failed: {e}")
        return {
            "code": 1,
            "message": f"Enhanced request failed: {str(e)}",
            "data": None,
        }


@router.get("/qa/enhancement")
def get_enhancement_info(
    query: str,
) -> dict[str, Any]:
    """Get enhancement information for query.

    Args:
        query: User query

    Returns:
        Enhancement metadata for frontend display
    """
    service = EnhancedRetrievalService()
    analysis = service.query_analyzer.analyze(query)

    return {
        "query": query,
        "detected_needs": {
            "chart": analysis.get("needs_chart", False),
            "table": analysis.get("needs_table", False),
            "image": analysis.get("needs_image", False),
        },
        "confidence": {
            "chart": analysis.get("chart_confidence", 0),
            "table": analysis.get("table_confidence", 0),
            "image": analysis.get("image_confidence", 0),
        },
        "features_enabled": {
            "modality_aware_ranking": settings.modality_aware_ranking_enabled,
            "vlm_image_description": settings.vlm_enabled,
        },
    }


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
