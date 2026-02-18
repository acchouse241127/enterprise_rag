"""
Async task service for background job management.

Phase 3.3: 异步任务队列
Author: C2
Date: 2026-02-14
"""

from datetime import datetime
from typing import Callable, Any
import threading
import logging

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.models.async_task import AsyncTask, TaskStatus, TaskType

logger = logging.getLogger(__name__)


class AsyncTaskService:
    """Service for managing async background tasks."""

    # In-memory task executor (simple thread-based)
    _executor_lock = threading.Lock()
    _running_tasks: dict[int, threading.Thread] = {}

    @staticmethod
    def create_task(
        db: Session,
        task_type: TaskType,
        entity_type: str | None = None,
        entity_id: int | None = None,
        input_data: dict | None = None,
        created_by: int | None = None,
    ) -> AsyncTask:
        """Create a new async task record."""
        task = AsyncTask(
            task_type=task_type.value,
            status=TaskStatus.PENDING.value,
            entity_type=entity_type,
            entity_id=entity_id,
            input_data=input_data,
            created_by=created_by,
            progress=0.0,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: int) -> AsyncTask | None:
        """Get a task by ID."""
        stmt = select(AsyncTask).where(AsyncTask.id == task_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_tasks(
        db: Session,
        task_type: TaskType | None = None,
        status: TaskStatus | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AsyncTask]:
        """List tasks with optional filters."""
        stmt = select(AsyncTask).order_by(desc(AsyncTask.created_at))

        if task_type:
            stmt = stmt.where(AsyncTask.task_type == task_type.value)
        if status:
            stmt = stmt.where(AsyncTask.status == status.value)
        if entity_type:
            stmt = stmt.where(AsyncTask.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(AsyncTask.entity_id == entity_id)

        stmt = stmt.limit(limit).offset(offset)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update_task_status(
        db: Session,
        task_id: int,
        status: TaskStatus,
        progress: float | None = None,
        message: str | None = None,
        output_data: dict | None = None,
        error_message: str | None = None,
    ) -> AsyncTask | None:
        """Update task status and progress."""
        task = AsyncTaskService.get_task(db, task_id)
        if not task:
            return None

        task.status = status.value
        if progress is not None:
            task.progress = progress
        if message is not None:
            task.message = message
        if output_data is not None:
            task.output_data = output_data
        if error_message is not None:
            task.error_message = error_message

        if status == TaskStatus.RUNNING and task.started_at is None:
            task.started_at = datetime.now()
        if status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED):
            task.completed_at = datetime.now()

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_pending_tasks_for_entity(
        db: Session, entity_type: str, entity_id: int
    ) -> list[AsyncTask]:
        """Get pending/running tasks for a specific entity."""
        stmt = (
            select(AsyncTask)
            .where(AsyncTask.entity_type == entity_type)
            .where(AsyncTask.entity_id == entity_id)
            .where(AsyncTask.status.in_([TaskStatus.PENDING.value, TaskStatus.RUNNING.value]))
            .order_by(desc(AsyncTask.created_at))
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def run_task_in_background(
        db_factory: Callable[[], Session],
        task_id: int,
        task_func: Callable[[Session, AsyncTask], Any],
    ) -> None:
        """
        Run a task function in a background thread.
        
        Args:
            db_factory: Function that creates a new database session
            task_id: The task ID to process
            task_func: Function that takes (db, task) and performs the work
        """
        def _worker():
            db = db_factory()
            try:
                task = AsyncTaskService.get_task(db, task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return

                # Mark as running
                AsyncTaskService.update_task_status(
                    db, task_id, TaskStatus.RUNNING, progress=0.0, message="任务开始执行"
                )

                # Execute the task
                try:
                    task_func(db, task)
                    # If task_func doesn't update status, mark as success
                    task = AsyncTaskService.get_task(db, task_id)
                    if task and task.status == TaskStatus.RUNNING.value:
                        AsyncTaskService.update_task_status(
                            db, task_id, TaskStatus.SUCCESS, progress=100.0, message="任务完成"
                        )
                except Exception as e:
                    logger.exception(f"Task {task_id} failed: {e}")
                    AsyncTaskService.update_task_status(
                        db, task_id, TaskStatus.FAILED, error_message=str(e)
                    )
            finally:
                db.close()
                with AsyncTaskService._executor_lock:
                    AsyncTaskService._running_tasks.pop(task_id, None)

        thread = threading.Thread(target=_worker, daemon=True)
        with AsyncTaskService._executor_lock:
            AsyncTaskService._running_tasks[task_id] = thread
        thread.start()

    @staticmethod
    def cancel_task(db: Session, task_id: int) -> bool:
        """Cancel a pending task (cannot cancel running tasks)."""
        task = AsyncTaskService.get_task(db, task_id)
        if not task:
            return False
        if task.status != TaskStatus.PENDING.value:
            return False

        AsyncTaskService.update_task_status(
            db, task_id, TaskStatus.CANCELLED, message="任务已取消"
        )
        return True
