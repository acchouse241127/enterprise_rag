"""Modality-aware retrieval enhancement for V2.1 Phase 4.

Integrates query analysis with retrieval to provide better results
for chart, table, and image specific queries.

Author: C2
Date: 2026-03-07
"""

import logging
from typing import Any

from ..config import settings
from .query_analyzer import QueryAnalyzer


logger = logging.getLogger(__name__)


class ModalityAwareRetrieval:
    """Modality-aware retrieval for enhanced RAG responses.

    Uses query analysis to boost retrieval results based on
    the type of content the user is asking for (charts, tables, images).
    """

    def __init__(self):
        """Initialize modality-aware retrieval."""
        self.query_analyzer = QueryAnalyzer()
        self._logger = logger

    def enhance_retrieval(
        self,
        query: str,
        retrieval_results: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Enhance retrieval results based on query modality.

        Args:
            query: User query string
            retrieval_results: Original retrieval results

        Returns:
            Tuple of (enhanced_results, enhancement_metadata)
        """
        # Analyze query to detect modality needs
        analysis = self.query_analyzer.analyze(query)

        enhancement_metadata = {
            "query": query,
            "original_result_count": len(retrieval_results),
            "needs_chart": analysis.get("needs_chart", False),
            "needs_table": analysis.get("needs_table", False),
            "needs_image": analysis.get("needs_image", False),
        }

        # If modality-aware ranking is disabled, return as-is
        if not settings.modality_aware_ranking_enabled:
            return retrieval_results, enhancement_metadata

        # Apply modality-aware boosting
        enhanced_results = self._apply_modality_boost(
            retrieval_results, analysis
        )

        enhancement_metadata["boosted_result_count"] = len(enhanced_results)
        enhancement_metadata["boost_applied"] = True

        self._logger.info(
            f"Modality-aware retrieval: {len(retrieval_results)} -> "
            f"{len(enhanced_results)} results"
        )

        return enhanced_results, enhancement_metadata

    def _apply_modality_boost(
        self,
        retrieval_results: list[dict[str, Any]],
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Apply modality-based boosting to retrieval results.

        Args:
            retrieval_results: Original retrieval results
            analysis: Query analysis with detected needs

        Returns:
            Reordered retrieval results with modality boosts applied
        """
        # Create a copy with boost scores
        boosted_results = []
        boost_types = self.query_analyzer.get_ranking_boost(analysis)

        for result in retrieval_results:
            content_type = result.get("content_type", "")
            metadata = result.get("metadata", {})
            original_score = result.get("score", 0.0)

            # Apply boost if content type matches query need
            boost_factor = 1.0
            if content_type.lower() in [bt.lower() for bt in boost_types]:
                boost_factor = settings.modality_boost_factor

            boosted_score = original_score * boost_factor

            boosted_result = {
                **result,
                "modality_boost": boost_factor,
                "original_score": original_score,
                "boosted_score": boosted_score,
                "metadata": {
                    **metadata,
                    "modality_boosted": boost_factor > 1.0,
                }
            }

            boosted_results.append(boosted_result)

        # Sort by boosted score (descending)
        boosted_results.sort(
            key=lambda x: x.get("boosted_score", 0),
            reverse=True,
        )

        self._logger.info(
            f"Applied modality boost: {boost_types} with factor "
            f"{settings.modality_boost_factor}"
        )

        return boosted_results

    def get_vlm_enhanced_chunks(
        self,
        retrieval_results: list[dict[str, Any]],
    ) -> list[str]:
        """Get VLM-enhanced text for image chunks.

        Args:
            retrieval_results: Retrieval results

        Returns:
            List of enhanced text chunks
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
                enhanced_text = f"{content}\n[VLM 描述]: {vlm_desc}"
                chunks.append(enhanced_text)
            else:
                chunks.append(content)

        return chunks

    def get_enhanced_context_builder(
        self,
        query: str,
        retrieval_results: list[dict[str, Any]],
    ):
        """Get a context builder function with modality awareness.

        Args:
            query: User query
            retrieval_results: Retrieval results

        Returns:
            Function that builds enhanced context
        """
        def build_context(results: list[dict[str, Any]]) -> str:
            if not results:
                return ""

            lines = []
            for idx, result in enumerate(results[:20]):
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                modality_boost = result.get("modality_boost", 1.0)

                # Add modality boost indicator
                boost_tag = ""
                if modality_boost > 1.0:
                    boost_tag = " [模态优先]"

                lines.append(f"[{idx}] {content}{boost_tag}")

            return "\n".join(lines)

        return build_context
