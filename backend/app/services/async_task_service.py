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

    @staticmethod
    def submit_document_parse_task(
        document_id: int,
        filename: str,
        created_by: int | None = None,
    ) -> AsyncTask:
        """
        创建并提交文档解析任务。

        Args:
            document_id: 文档ID
            filename: 文件名（用于前端显示）
            created_by: 创建者用户ID

        Returns:
            AsyncTask: 创建的任务记录
        """
        from app.core.database import SessionLocal

        # 创建临时会话来创建任务
        db = SessionLocal()
        try:
            task = AsyncTaskService.create_task(
                db=db,
                task_type=TaskType.DOCUMENT_PARSE,
                entity_type="document",
                entity_id=document_id,
                input_data={"filename": filename, "document_id": document_id},
                created_by=created_by,
            )
            task_id = task.id
        finally:
            db.close()

        # 在后台线程中执行任务
        def _parse_document_task(db: Session, task: AsyncTask):
            """文档解析任务执行函数"""
            from app.services.document_service import DocumentService

            document_id = task.entity_id
            if not document_id:
                raise ValueError("任务缺少 document_id")

            # 更新进度：开始解析
            AsyncTaskService.update_task_status(
                db, task.id, TaskStatus.RUNNING,
                progress=10.0, message="正在解析文档..."
            )

            try:
                # 执行文档解析
                DocumentService.parse_and_index_sync(db, document_id)

                # 获取文档状态
                doc = DocumentService.get_by_id(db, document_id)
                if doc and doc.status == "vectorized":
                    AsyncTaskService.update_task_status(
                        db, task.id, TaskStatus.SUCCESS,
                        progress=100.0, message="文档解析完成",
                        output_data={"document_id": document_id, "status": "vectorized"}
                    )
                elif doc and doc.status == "parsed":
                    AsyncTaskService.update_task_status(
                        db, task.id, TaskStatus.SUCCESS,
                        progress=100.0, message="文档解析完成（向量化跳过）",
                        output_data={"document_id": document_id, "status": "parsed"}
                    )
                elif doc and doc.status == "parse_failed":
                    AsyncTaskService.update_task_status(
                        db, task.id, TaskStatus.FAILED,
                        progress=100.0,
                        error_message=doc.parser_message or "文档解析失败"
                    )
                else:
                    AsyncTaskService.update_task_status(
                        db, task.id, TaskStatus.SUCCESS,
                        progress=100.0, message="文档处理完成",
                        output_data={"document_id": document_id, "status": doc.status if doc else "unknown"}
                    )
            except Exception as e:
                logger.exception(f"文档解析任务失败: document_id={document_id}, error={e}")
                AsyncTaskService.update_task_status(
                    db, task.id, TaskStatus.FAILED,
                    error_message=str(e)
                )
                raise

        # 使用 SessionLocal 作为 db_factory
        AsyncTaskService.run_task_in_background(
            db_factory=SessionLocal,
            task_id=task_id,
            task_func=_parse_document_task
        )

        # 返回任务（需要重新查询）
        db = SessionLocal()
        try:
            return AsyncTaskService.get_task(db, task_id)
        finally:
            db.close()
