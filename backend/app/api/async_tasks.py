"""
Async task API endpoints.

Phase 3.3: 异步任务队列
Author: C2
Date: 2026-02-14
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User
from app.models.async_task import TaskStatus, TaskType
from app.services.async_task_service import AsyncTaskService

router = APIRouter(prefix="/tasks", tags=["async-tasks"])


# ============== Schemas ==============
class TaskResponse(BaseModel):
    id: int
    task_type: str
    status: str
    entity_type: str | None
    entity_id: int | None
    progress: float
    message: str | None
    error_message: str | None
    started_at: str | None
    completed_at: str | None
    created_at: str

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int


# ============== Endpoints ==============
@router.get("", response_model=TaskListResponse)
def list_tasks(
    task_type: str | None = None,
    status: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List async tasks with optional filters."""
    task_type_enum = TaskType(task_type) if task_type else None
    status_enum = TaskStatus(status) if status else None

    tasks = AsyncTaskService.list_tasks(
        db,
        task_type=task_type_enum,
        status=status_enum,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )

    return TaskListResponse(
        tasks=[
            TaskResponse(
                id=t.id,
                task_type=t.task_type,
                status=t.status,
                entity_type=t.entity_type,
                entity_id=t.entity_id,
                progress=t.progress,
                message=t.message,
                error_message=t.error_message,
                started_at=t.started_at.isoformat() if t.started_at else None,
                completed_at=t.completed_at.isoformat() if t.completed_at else None,
                created_at=t.created_at.isoformat(),
            )
            for t in tasks
        ],
        total=len(tasks),
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task details by ID."""
    task = AsyncTaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status,
        entity_type=task.entity_type,
        entity_id=task.entity_id,
        progress=task.progress,
        message=task.message,
        error_message=task.error_message,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
    )


@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending task."""
    success = AsyncTaskService.cancel_task(db, task_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法取消任务（任务不存在或已在执行中）")

    return {"message": "任务已取消"}


@router.get("/entity/{entity_type}/{entity_id}")
def get_entity_tasks(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending/running tasks for a specific entity."""
    tasks = AsyncTaskService.get_pending_tasks_for_entity(db, entity_type, entity_id)
    return {
        "tasks": [
            {
                "id": t.id,
                "task_type": t.task_type,
                "status": t.status,
                "progress": t.progress,
                "message": t.message,
            }
            for t in tasks
        ]
    }
