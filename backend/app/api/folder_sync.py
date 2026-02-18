"""
Folder sync APIs.

Phase 3.2: 文件夹同步（轮询 + 手动）
Author: C2
Date: 2026-02-13
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_editor_user
from app.models.user import User
from app.services.folder_sync_service import FolderSyncService

router = APIRouter()


class FolderSyncConfigCreate(BaseModel):
    """Request body for creating/updating folder sync config."""
    directory_path: str
    enabled: bool = True
    sync_interval_minutes: int | None = None
    file_patterns: str | None = None


class FolderSyncConfigResponse(BaseModel):
    """Response model for folder sync config."""
    id: int
    knowledge_base_id: int
    directory_path: str
    enabled: bool
    sync_interval_minutes: int
    file_patterns: str
    last_sync_at: str | None
    last_sync_status: str
    last_sync_message: str | None
    last_sync_files_added: int
    last_sync_files_updated: int
    last_sync_files_deleted: int


@router.get("/knowledge-bases/{knowledge_base_id}/folder-sync")
def get_folder_sync_config(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get folder sync configuration for a knowledge base."""
    config = FolderSyncService.get_config(db, knowledge_base_id)
    if config is None:
        return {"code": 0, "message": "success", "data": None}

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": config.id,
            "knowledge_base_id": config.knowledge_base_id,
            "directory_path": config.directory_path,
            "enabled": config.enabled,
            "sync_interval_minutes": config.sync_interval_minutes,
            "file_patterns": config.file_patterns,
            "last_sync_at": config.last_sync_at.isoformat() if config.last_sync_at else None,
            "last_sync_status": config.last_sync_status,
            "last_sync_message": config.last_sync_message,
            "last_sync_files_added": config.last_sync_files_added,
            "last_sync_files_updated": config.last_sync_files_updated,
            "last_sync_files_deleted": config.last_sync_files_deleted,
        },
    }


@router.post("/knowledge-bases/{knowledge_base_id}/folder-sync")
def create_or_update_folder_sync_config(
    knowledge_base_id: int,
    body: FolderSyncConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_editor_user),
) -> dict:
    """Create or update folder sync configuration."""
    config, err = FolderSyncService.create_or_update_config(
        db=db,
        knowledge_base_id=knowledge_base_id,
        directory_path=body.directory_path,
        enabled=body.enabled,
        sync_interval_minutes=body.sync_interval_minutes,
        file_patterns=body.file_patterns,
    )
    if err:
        return {"code": 4001, "message": "配置失败", "detail": err}

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": config.id,
            "knowledge_base_id": config.knowledge_base_id,
            "directory_path": config.directory_path,
            "enabled": config.enabled,
            "sync_interval_minutes": config.sync_interval_minutes,
            "file_patterns": config.file_patterns,
        },
    }


@router.delete("/knowledge-bases/{knowledge_base_id}/folder-sync")
def delete_folder_sync_config(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_editor_user),
) -> dict:
    """Delete folder sync configuration."""
    success, err = FolderSyncService.delete_config(db, knowledge_base_id)
    if not success:
        return {"code": 4040, "message": "删除失败", "detail": err}
    return {"code": 0, "message": "success", "data": {"deleted": True}}


@router.post("/knowledge-bases/{knowledge_base_id}/folder-sync/trigger")
def trigger_folder_sync(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_editor_user),
) -> dict:
    """Manually trigger folder synchronization."""
    log, err = FolderSyncService.sync_folder(db, knowledge_base_id, triggered_by="manual")
    if err:
        return {"code": 4001, "message": "同步失败", "detail": err}

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": log.id,
            "status": log.status,
            "message": log.message,
            "files_scanned": log.files_scanned,
            "files_added": log.files_added,
            "files_updated": log.files_updated,
            "files_deleted": log.files_deleted,
            "files_failed": log.files_failed,
            "duration_seconds": log.duration_seconds,
            "triggered_by": log.triggered_by,
            "created_at": log.created_at.isoformat(),
        },
    }


@router.get("/knowledge-bases/{knowledge_base_id}/folder-sync/logs")
def get_folder_sync_logs(
    knowledge_base_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get folder sync logs for a knowledge base."""
    logs = FolderSyncService.get_sync_logs(db, knowledge_base_id, limit=limit)
    return {
        "code": 0,
        "message": "success",
        "data": [
            {
                "id": log.id,
                "status": log.status,
                "message": log.message,
                "files_scanned": log.files_scanned,
                "files_added": log.files_added,
                "files_updated": log.files_updated,
                "files_deleted": log.files_deleted,
                "files_failed": log.files_failed,
                "duration_seconds": log.duration_seconds,
                "triggered_by": log.triggered_by,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }
