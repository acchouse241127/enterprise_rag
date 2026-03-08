"""Enhanced retrieval service with modality awareness and VLM support.

Integrates query analysis, modality-aware ranking, and VLM
image description into the RAG pipeline for better responses.

Author: C2
Date: 2026-03-07
"""

import logging
from typing import Any

from app.config import settings
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.modality_aware_retrieval import ModalityAwareRetrieval
from app.rag.embedding import BgeM3EmbeddingService
from app.rag.retriever import VectorRetriever
from app.rag.vector_store import ChromaVectorStore


logger = logging.getLogger(__name__)


class EnhancedRetrievalService:
    """Enhanced retrieval service for V2.1 Phase 4.

    Provides modality-aware retrieval and VLM-enhanced content
    for better RAG responses.
    """

    def __init__(self):
        """Initialize enhanced retrieval service."""
        self.query_analyzer = QueryAnalyzer()
        self.modality_retrieval = ModalityAwareRetrieval()
        self._logger = logger

        # Initialize components
        self._embedding_service = BgeM3EmbeddingService(
            model_name=settings.embedding_model_name,
            fallback_dim=settings.embedding_fallback_dim,
        )
        self._vector_store = ChromaVectorStore(
            host=settings.chroma_host,
            port=settings.chroma_port,
            collection_prefix=settings.chroma_collection_prefix,
        )
        self._retriever = VectorRetriever(
            self._embedding_service,
            self._vector_store,
        )

    def retrieve_with_modality_aware(
        self,
        query: str,
        knowledge_base_id: int,
        top_k: int = 5,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Retrieve chunks with modality-aware ranking.

        Args:
            query: User query
            knowledge_base_id: Knowledge base ID
            top_k: Number of results to return

        Returns:
            Tuple of (retrieved_chunks, enhancement_metadata)
        """
        # Step 1: Initial retrieval
        raw_results = self._retriever.retrieve(query, knowledge_base_id, top_k=top_k)

        # Step 2: Analyze query and apply modality boost
        enhanced_results, metadata = self.modality_retrieval.enhance_retrieval(
            query, raw_results
        )

        self._logger.info(
            f"Modality-aware retrieval: {len(raw_results)} -> "
            f"{len(enhanced_results)} chunks"
        )

        return enhanced_results, metadata

    def get_vlm_enhanced_chunks(
        self,
        retrieval_results: list[dict[str, Any]],
    ) -> list[str]:
        """Get VLM-enhanced text chunks from retrieval results.

        Args:
            retrieval_results: Retrieval results

        Returns:
            List of text chunks with VLM enhancements for images
        """
        if not settings.vlm_enabled:
            # VLM not enabled, return original content
            return [r.get("content", "") for r in retrieval_results]

        chunks = []
        for result in retrieval_results:
            content_type = result.get("content_type", "")
            content = result.get("content", "")
            metadata = result.get("metadata", {})

            if content_type == "image" and "vlm_description" in metadata:
                # Merge OCR text with VLM description
                vlm_desc = metadata["vlm_description"]
                enhanced_text = f"{content}\n[VLM]: {vlm_desc}"
                chunks.append(enhanced_text)
            else:
                chunks.append(content)

        return chunks

    def get_enhancement_info(self, query: str) -> dict[str, Any]:
        """Get enhancement information for frontend display.

        Args:
            query: User query

        Returns:
            Dict with enhancement metadata for frontend
        """
        analysis = self.query_analyzer.analyze(query)

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

    def format_retrieval_result(
        self,
        result: dict[str, Any],
        enhancement_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format retrieval result for frontend display.

        Args:
            result: Single retrieval result
            enhancement_metadata: Enhancement metadata from modality-aware retrieval

        Returns:
            Formatted result dict
        """
        formatted = {
            **result,
            "content_type": result.get("content_type", "text"),
        }

        # Add modality boost indicator if available
        if enhancement_metadata:
            formatted["modality_boosted"] = enhancement_metadata.get("boost_applied", False)
            if result.get("modality_boost", 1.0) > 1.0:
                formatted["modality_boosted"] = True

        # Add VLM enhancement indicator if available
        if result.get("content_type") == "image":
            metadata = result.get("metadata", {})
            formatted["has_vlm_description"] = "vlm_description" in metadata
            formatted["vlm_available"] = settings.vlm_enabled

        return formatted
