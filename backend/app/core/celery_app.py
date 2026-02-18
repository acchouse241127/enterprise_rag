"""Celery application for async document parse and index tasks."""

from celery import Celery

from app.config import settings

broker = settings.celery_broker_url or settings.redis_url
backend = settings.redis_url

celery_app = Celery(
    "enterprise_rag",
    broker=broker,
    backend=backend,
    include=["app.tasks.document_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task
def noop() -> str:
    """No-op task for worker liveness check."""
    return "ok"
