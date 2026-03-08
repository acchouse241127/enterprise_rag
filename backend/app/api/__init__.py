"""API router package."""

from fastapi import APIRouter

from .auth import router as auth_router
from .document import router as document_router
from .knowledge_base import router as knowledge_base_router
from .qa import router as qa_router
from .system import router as system_router
from .folder_sync import router as folder_sync_router
from .retrieval import router as retrieval_router
# Phase 3.3
from .async_tasks import router as async_tasks_router
from .conversations import router as conversations_router
from .metrics import router as metrics_router
from .kb_edit import router as kb_edit_router
from .docker_mount import router as docker_mount_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(knowledge_base_router, prefix="/knowledge-bases", tags=["knowledge_bases"])
api_router.include_router(document_router, tags=["documents"])
api_router.include_router(qa_router, tags=["qa"])
api_router.include_router(system_router, prefix="/system", tags=["system"])
# Phase 3.2
api_router.include_router(folder_sync_router, tags=["folder_sync"])
api_router.include_router(retrieval_router, tags=["retrieval"])
# Phase 3.3
api_router.include_router(async_tasks_router, tags=["async_tasks"])
api_router.include_router(conversations_router, tags=["conversations"])
api_router.include_router(metrics_router, tags=["metrics"])
api_router.include_router(kb_edit_router, tags=["kb_edit"])
api_router.include_router(docker_mount_router, prefix="/docker", tags=["docker_mount"])

