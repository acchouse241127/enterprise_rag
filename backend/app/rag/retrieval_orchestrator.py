"""Retrieval orchestrator with multi-level fallback strategy.

Implements degradation strategy:
- L0: Normal (vector retrieval)
- L1: Vector timeout -> BM25 fallback
- L2: Vector unavailable -> BM25 fallback
- L3: All failed -> Error

Author: C2
Date: 2026-03-03
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class DegradationLevel(str, Enum):
    """Degradation level enum."""

    L0_NORMAL = "L0_NORMAL"
    L1_VECTOR_TIMEOUT = "L1_VECTOR_TIMEOUT"
    L2_VECTOR_UNAVAILABLE = "L2_VECTOR_UNAVAILABLE"
    L3_ALL_FAILED = "L3_ALL_FAILED"


@dataclass
class DegradationInfo:
    """Information about degradation state."""

    level: DegradationLevel
    reason: str
    fallback_used: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": self.level.value,
            "reason": self.reason,
            "fallback_used": self.fallback_used,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DegradationInfo":
        """Create from dictionary."""
        level = DegradationLevel(data["level"])
        return cls(
            level=level,
            reason=data["reason"],
            fallback_used=data.get("fallback_used"),
            timestamp=data.get("timestamp", time.time()),
        )


class HealthChecker:
    """Health checker for retrieval backends."""

    def __init__(
        self,
        vector_retriever=None,
        check_interval_seconds: Optional[int] = None,
    ):
        self._vector_retriever = vector_retriever
        self._check_interval = check_interval_seconds or settings.health_check_interval_seconds
        self._last_check_time = 0
        self._is_healthy = True
        self._lock = threading.Lock()

    def is_healthy(self) -> bool:
        """Check if vector retriever is healthy."""
        if self._vector_retriever is None:
            return False

        # Check if we have a health_check method
        if hasattr(self._vector_retriever, "health_check"):
            try:
                return bool(self._vector_retriever.health_check())
            except Exception as e:
                logger.warning(f"Health check failed: {e}")
                return False

        # Default to healthy if no health check method
        return True

    def check_and_update(self) -> bool:
        """Check health and update internal state."""
        with self._lock:
            current_time = time.time()
            if current_time - self._last_check_time >= self._check_interval:
                self._is_healthy = self.is_healthy()
                self._last_check_time = current_time
            return self._is_healthy


class RetrievalOrchestrator:
    """Orchestrates retrieval with multi-level fallback strategy."""

    def __init__(
        self,
        vector_retriever=None,
        bm25_retriever=None,
        timeout_ms: Optional[int] = None,
        fallback_enabled: Optional[bool] = None,
    ):
        self._vector_retriever = vector_retriever
        self._bm25_retriever = bm25_retriever
        self.timeout_ms = timeout_ms or settings.retrieval_timeout_ms
        self.fallback_enabled = (
            fallback_enabled if fallback_enabled is not None
            else settings.retrieval_fallback_enabled
        )
        self._health_checker = HealthChecker(vector_retriever)

    def _retrieve_with_timeout(
        self,
        retriever,
        kb_id: int,
        query: str,
        top_k: int,
    ) -> Tuple[Optional[list], Optional[str]]:
        """Retrieve with timeout handling."""
        if retriever is None:
            return None, "Retriever not available"

        timeout_seconds = self.timeout_ms / 1000.0

        result_container = {"result": None, "error": None}
        exception_container = {"exception": None}

        def retrieve_task():
            try:
                result = retriever.retrieve(kb_id=kb_id, query=query, top_k=top_k)
                result_container["result"] = result
            except Exception as e:
                exception_container["exception"] = e

        thread = threading.Thread(target=retrieve_task)
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            # Thread is still running, timeout occurred
            logger.warning(f"Retrieval timeout after {self.timeout_ms}ms")
            return None, f"Timeout after {self.timeout_ms}ms"

        if exception_container["exception"]:
            return None, str(exception_container["exception"])

        return result_container["result"]

    def _try_bm25_fallback(
        self,
        kb_id: int,
        query: str,
        top_k: int,
        reason: str,
    ) -> Tuple[Optional[list], DegradationInfo]:
        """Try BM25 fallback retrieval."""
        if self._bm25_retriever is None:
            return None, DegradationInfo(
                level=DegradationLevel.L3_ALL_FAILED,
                reason=f"BM25 fallback unavailable: {reason}",
                fallback_used=None,
            )

        try:
            result = self._bm25_retriever.retrieve(kb_id=kb_id, query=query, top_k=top_k)
            if result is None:
                return None, DegradationInfo(
                    level=DegradationLevel.L3_ALL_FAILED,
                    reason="BM25 retrieval returned None",
                    fallback_used="bm25",
                )

            chunks, error = result
            if error:
                return None, DegradationInfo(
                    level=DegradationLevel.L3_ALL_FAILED,
                    reason=f"BM25 retrieval failed: {error}",
                    fallback_used="bm25",
                )

            # Determine degradation level based on original reason
            if "timeout" in reason.lower():
                level = DegradationLevel.L1_VECTOR_TIMEOUT
            else:
                level = DegradationLevel.L2_VECTOR_UNAVAILABLE

            return chunks, DegradationInfo(
                level=level,
                reason=reason,
                fallback_used="bm25",
            )

        except Exception as e:
            return None, DegradationInfo(
                level=DegradationLevel.L3_ALL_FAILED,
                reason=f"BM25 fallback exception: {e}",
                fallback_used="bm25",
            )

    def retrieve(
        self,
        kb_id: int,
        query: str,
        top_k: Optional[int] = None,
    ) -> Tuple[Optional[list], DegradationInfo]:
        """
        Retrieve chunks with fallback strategy.

        Returns:
            Tuple of (chunks, degradation_info)
        """
        top_k = top_k or settings.retrieval_top_k

        # Check health first
        if not self._health_checker.check_and_update():
            if self.fallback_enabled:
                return self._try_bm25_fallback(
                    kb_id, query, top_k,
                    "Vector store health check failed"
                )
            return None, DegradationInfo(
                level=DegradationLevel.L2_VECTOR_UNAVAILABLE,
                reason="Vector store unhealthy and fallback disabled",
                fallback_used=None,
            )

        # Try vector retrieval with timeout
        if self._vector_retriever is None:
            if self.fallback_enabled and self._bm25_retriever:
                return self._try_bm25_fallback(
                    kb_id, query, top_k,
                    "Vector retriever not configured"
                )
            return None, DegradationInfo(
                level=DegradationLevel.L3_ALL_FAILED,
                reason="No retriever available",
                fallback_used=None,
            )

        result = self._retrieve_with_timeout(
            self._vector_retriever, kb_id, query, top_k
        )

        if result is None:
            return None, DegradationInfo(
                level=DegradationLevel.L3_ALL_FAILED,
                reason="Retrieval returned None",
                fallback_used=None,
            )

        chunks, error = result

        if error:
            if self.fallback_enabled:
                return self._try_bm25_fallback(kb_id, query, top_k, error)
            return None, DegradationInfo(
                level=DegradationLevel.L3_ALL_FAILED,
                reason=error,
                fallback_used=None,
            )

        if chunks is None:
            chunks = []

        # Normal success
        return chunks, DegradationInfo(
            level=DegradationLevel.L0_NORMAL,
            reason="Success",
            fallback_used=None,
        )

    def update_retrievers(
        self,
        vector_retriever=None,
        bm25_retriever=None,
    ) -> None:
        """Update retrievers (for dynamic configuration)."""
        if vector_retriever is not None:
            self._vector_retriever = vector_retriever
            self._health_checker = HealthChecker(vector_retriever)
        if bm25_retriever is not None:
            self._bm25_retriever = bm25_retriever


def create_orchestrator(
    vector_retriever=None,
    bm25_retriever=None,
    **kwargs,
) -> RetrievalOrchestrator:
    """Factory function to create retrieval orchestrator."""
    return RetrievalOrchestrator(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        **kwargs,
    )
