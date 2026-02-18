"""
Prometheus metrics endpoint.

Phase 3.3: Prometheus + Grafana 监控
Author: C2
Date: 2026-02-14
"""

from fastapi import APIRouter, Response

from app.metrics import get_metrics, get_content_type

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def prometheus_metrics():
    """Expose Prometheus metrics."""
    return Response(
        content=get_metrics(),
        media_type=get_content_type(),
    )
