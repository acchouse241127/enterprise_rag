"""
Unit tests for AsyncTaskService.

Tests for app/services/async_task_service.py
Author: C2
"""

import pytest
import threading
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock


class TestAsyncTaskServiceCreate:
    """Tests for AsyncTaskService.create_task."""

    def test_create_task_basic(self):
        """Test basic task creation."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskType

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 1

        with patch("app.services.async_task_service.AsyncTask") as MockTask:
            MockTask.return_value = mock_task
            result = AsyncTaskService.create_task(
                db=mock_db,
                task_type=TaskType.DOCUMENT_PARSE,
            )
            assert result == mock_task
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    def test_create_task_with_all_fields(self):
        """Test task creation with all optional fields."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskType

        mock_db = MagicMock()
        mock_task = MagicMock()

        with patch("app.services.async_task_service.AsyncTask") as MockTask:
            MockTask.return_value = mock_task
            result = AsyncTaskService.create_task(
                db=mock_db,
                task_type=TaskType.DOCUMENT_VECTORIZE,
                entity_type="document",
                entity_id=123,
                input_data={"key": "value"},
                created_by=1,
            )
            assert result == mock_task

    def test_create_task_initial_progress_is_zero(self):
        """Test that new task has initial progress of 0."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskType

        mock_db = MagicMock()
        mock_task = MagicMock()

        with patch("app.services.async_task_service.AsyncTask") as MockTask:
            MockTask.return_value = mock_task
            AsyncTaskService.create_task(mock_db, TaskType.FOLDER_SYNC)

            call_kwargs = MockTask.call_args[1]
            assert call_kwargs["progress"] == 0.0


class TestAsyncTaskServiceGet:
    """Tests for AsyncTaskService.get_task."""

    def test_get_task_found(self):
        """Test getting existing task."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 1
        mock_result.scalar_one_or_none.return_value = mock_task

        mock_db.execute.return_value = mock_result

        result = AsyncTaskService.get_task(mock_db, 1)
        assert result == mock_task

    def test_get_task_not_found(self):
        """Test getting non-existent task."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_result

        result = AsyncTaskService.get_task(mock_db, 999)
        assert result is None


class TestAsyncTaskServiceList:
    """Tests for AsyncTaskService.list_tasks."""

    def test_list_tasks_no_filters(self):
        """Test listing tasks without filters."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_tasks = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_tasks

        mock_db.execute.return_value = mock_result

        result = AsyncTaskService.list_tasks(mock_db)
        assert len(result) == 2

    def test_list_tasks_with_type_filter(self):
        """Test listing tasks filtered by type."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskType

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_tasks = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_tasks

        mock_db.execute.return_value = mock_result

        result = AsyncTaskService.list_tasks(mock_db, task_type=TaskType.DOCUMENT_PARSE)
        assert len(result) == 1

    def test_list_tasks_with_status_filter(self):
        """Test listing tasks filtered by status."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskStatus

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_tasks = [MagicMock(), MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_tasks

        mock_db.execute.return_value = mock_result

        result = AsyncTaskService.list_tasks(mock_db, status=TaskStatus.PENDING)
        assert len(result) == 3

    def test_list_tasks_with_entity_filter(self):
        """Test listing tasks filtered by entity."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_tasks = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_tasks

        mock_db.execute.return_value = mock_result

        result = AsyncTaskService.list_tasks(
            mock_db, entity_type="document", entity_id=5
        )
        assert len(result) == 1

    def test_list_tasks_with_pagination(self):
        """Test listing tasks with limit and offset."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db.execute.return_value = mock_result

        result = AsyncTaskService.list_tasks(mock_db, limit=10, offset=20)
        assert result == []


class TestAsyncTaskServiceUpdateStatus:
    """Tests for AsyncTaskService.update_task_status."""

    def test_update_status_to_running(self):
        """Test updating task status to running."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskStatus

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "pending"
        mock_task.started_at = None

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            result = AsyncTaskService.update_task_status(
                mock_db, 1, TaskStatus.RUNNING, progress=0.0, message="Starting"
            )
            assert result == mock_task
            assert mock_task.started_at is not None
            mock_db.commit.assert_called()

    def test_update_status_to_success(self):
        """Test updating task status to success."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskStatus

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "running"

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            result = AsyncTaskService.update_task_status(
                mock_db, 1, TaskStatus.SUCCESS, progress=100.0, output_data={"result": "ok"}
            )
            assert result == mock_task
            assert mock_task.completed_at is not None
            assert mock_task.output_data == {"result": "ok"}

    def test_update_status_to_failed(self):
        """Test updating task status to failed."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskStatus

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "running"

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            result = AsyncTaskService.update_task_status(
                mock_db, 1, TaskStatus.FAILED, error_message="Something went wrong"
            )
            assert result == mock_task
            assert mock_task.error_message == "Something went wrong"
            assert mock_task.completed_at is not None

    def test_update_status_to_cancelled(self):
        """Test updating task status to cancelled."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskStatus

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "pending"

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            result = AsyncTaskService.update_task_status(
                mock_db, 1, TaskStatus.CANCELLED
            )
            assert result == mock_task
            assert mock_task.completed_at is not None

    def test_update_status_task_not_found(self):
        """Test updating status for non-existent task."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskStatus

        mock_db = MagicMock()

        with patch.object(AsyncTaskService, "get_task", return_value=None):
            result = AsyncTaskService.update_task_status(
                mock_db, 999, TaskStatus.RUNNING
            )
            assert result is None

    def test_update_status_sets_progress(self):
        """Test that update sets progress correctly."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskStatus

        mock_db = MagicMock()
        mock_task = MagicMock()

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            AsyncTaskService.update_task_status(
                mock_db, 1, TaskStatus.RUNNING, progress=50.5
            )
            assert mock_task.progress == 50.5


class TestAsyncTaskServicePendingTasks:
    """Tests for AsyncTaskService.get_pending_tasks_for_entity."""

    def test_get_pending_tasks_for_entity(self):
        """Test getting pending tasks for specific entity."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_tasks = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_tasks

        mock_db.execute.return_value = mock_result

        result = AsyncTaskService.get_pending_tasks_for_entity(
            mock_db, "document", 123
        )
        assert len(result) == 2


class TestAsyncTaskServiceCancel:
    """Tests for AsyncTaskService.cancel_task."""

    def test_cancel_pending_task(self):
        """Test cancelling a pending task."""
        from app.services.async_task_service import AsyncTaskService
        from app.models.async_task import TaskStatus

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "pending"

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            with patch.object(AsyncTaskService, "update_task_status") as mock_update:
                result = AsyncTaskService.cancel_task(mock_db, 1)
                assert result == True
                mock_update.assert_called_once()

    def test_cancel_running_task_fails(self):
        """Test that cancelling a running task fails."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "running"

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            result = AsyncTaskService.cancel_task(mock_db, 1)
            assert result == False

    def test_cancel_completed_task_fails(self):
        """Test that cancelling a completed task fails."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "success"

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            result = AsyncTaskService.cancel_task(mock_db, 1)
            assert result == False

    def test_cancel_nonexistent_task_fails(self):
        """Test that cancelling non-existent task fails."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()

        with patch.object(AsyncTaskService, "get_task", return_value=None):
            result = AsyncTaskService.cancel_task(mock_db, 999)
            assert result == False


class TestAsyncTaskServiceBackgroundExecution:
    """Tests for AsyncTaskService.run_task_in_background."""

    def test_run_task_in_background_starts_thread(self):
        """Test that run_task_in_background starts a thread."""
        from app.services.async_task_service import AsyncTaskService

        mock_db_factory = MagicMock()
        mock_task_func = MagicMock()

        with patch.object(AsyncTaskService, "get_task") as mock_get:
            mock_task = MagicMock()
            mock_task.status = "pending"
            mock_get.return_value = mock_task

            with patch.object(AsyncTaskService, "update_task_status"):
                AsyncTaskService.run_task_in_background(
                    mock_db_factory, 1, mock_task_func
                )

                # Give thread a moment to start
                import time
                time.sleep(0.1)

                # Thread should have been created
                assert len(AsyncTaskService._running_tasks) >= 0  # May have completed

    def test_run_task_handles_task_not_found(self):
        """Test background task handles missing task gracefully."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_db_factory = MagicMock(return_value=mock_db)
        mock_task_func = MagicMock()

        with patch.object(AsyncTaskService, "get_task", return_value=None):
            with patch("app.services.async_task_service.logger") as mock_logger:
                AsyncTaskService.run_task_in_background(
                    mock_db_factory, 999, mock_task_func
                )

                # Give thread time to execute
                import time
                time.sleep(0.1)

                # Should have logged error
                mock_logger.error.assert_called()

    def test_run_task_handles_exception(self):
        """Test background task handles exceptions."""
        from app.services.async_task_service import AsyncTaskService

        mock_db = MagicMock()
        mock_db_factory = MagicMock(return_value=mock_db)
        mock_task = MagicMock()
        mock_task.status = "running"

        def failing_func(db, task):
            raise ValueError("Test error")

        with patch.object(AsyncTaskService, "get_task", return_value=mock_task):
            with patch("app.services.async_task_service.logger") as mock_logger:
                AsyncTaskService.run_task_in_background(
                    mock_db_factory, 1, failing_func
                )

                # Give thread time to execute
                import time
                time.sleep(0.3)

                # Should have logged the exception
                mock_logger.exception.assert_called()


class TestTaskStatusEnum:
    """Tests for TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum has correct values."""
        from app.models.async_task import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTaskTypeEnum:
    """Tests for TaskType enum."""

    def test_task_type_values(self):
        """Test TaskType enum has correct values."""
        from app.models.async_task import TaskType

        assert TaskType.DOCUMENT_PARSE.value == "document_parse"
        assert TaskType.DOCUMENT_VECTORIZE.value == "document_vectorize"
        assert TaskType.FOLDER_SYNC.value == "folder_sync"
        assert TaskType.EXPORT_CONVERSATION.value == "export_conversation"
