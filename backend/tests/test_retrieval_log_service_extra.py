"""
Additional unit tests for RetrievalLogService.

Tests for app/services/retrieval_log_service.py
Author: C2
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestRetrievalLogServiceCreate:
    """Tests for create_log method."""

    def test_create_log_success(self):
        """Test successful log creation."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()
        mock_log.id = 1

        with patch('app.services.retrieval_log_service.RetrievalLog') as MockLog:
            MockLog.return_value = mock_log
            with patch('app.services.retrieval_log_service.settings') as mock_settings:
                mock_settings.retrieval_log_max_chunks = 10

                result = RetrievalLogService.create_log(
                    db=mock_db,
                    knowledge_base_id=1,
                    user_id=1,
                    query="test query",
                    chunks_retrieved=5,
                    chunks_after_filter=4,
                    chunks_after_dedup=3,
                    chunks_after_rerank=2,
                    top_chunk_score=0.9,
                    avg_chunk_score=0.7,
                    min_chunk_score=0.5,
                    chunk_details=[],
                )

                assert result == mock_log
                mock_db.add.assert_called()
                mock_db.commit.assert_called()

    def test_create_log_with_chunk_details(self):
        """Test log creation with chunk details."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        chunk_details = [
            {"chunk_id": 1, "document_id": 1, "content_preview": "test", "score": 0.9}
        ]

        with patch('app.services.retrieval_log_service.RetrievalLog') as MockLog:
            MockLog.return_value = mock_log
            with patch('app.services.retrieval_log_service.settings') as mock_settings:
                mock_settings.retrieval_log_max_chunks = 10
                result = RetrievalLogService.create_log(
                    db=mock_db,
                    knowledge_base_id=1,
                    user_id=1,
                    query="test",
                    chunks_retrieved=1,
                    chunks_after_filter=1,
                    chunks_after_dedup=1,
                    chunks_after_rerank=1,
                    chunk_details=chunk_details,
                )

                assert result == mock_log

    def test_create_log_with_timing(self):
        """Test log creation with timing info."""
        from app.services.retrieval_log_service import RetrievalLogService
        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch('app.services.retrieval_log_service.RetrievalLog') as MockLog:
            MockLog.return_value = mock_log
            with patch('app.services.retrieval_log_service.settings') as mock_settings:
                mock_settings.retrieval_log_max_chunks = 10
                result = RetrievalLogService.create_log(
                    db=mock_db,
                    knowledge_base_id=1,
                    user_id=1,
                    query="test",
                    chunks_retrieved=1,
                    chunks_after_filter=1,
                    chunks_after_dedup=1,
                    chunks_after_rerank=1,
                    retrieval_time_ms=100,
                    rerank_time_ms=50,
                    total_time_ms=200,
                )

                assert result == mock_log

    def test_create_log_with_answer_info(self):
        """Test log creation with answer info."""
        from app.services.retrieval_log_service import RetrievalLogService
        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch('app.services.retrieval_log_service.RetrievalLog') as MockLog:
            MockLog.return_value = mock_log
            with patch('app.services.retrieval_log_service.settings') as mock_settings:
                mock_settings.retrieval_log_max_chunks = 10
                result = RetrievalLogService.create_log(
                    db=mock_db,
                    knowledge_base_id=1,
                    user_id=1,
                    query="test",
                    chunks_retrieved=1,
                    chunks_after_filter=1,
                    chunks_after_dedup=1,
                    chunks_after_rerank=1,
                    answer_generated=True,
                    answer_length=100,
                    cited_chunk_ids=[1, 2, 3],
                )

                assert result == mock_log


class TestRetrievalLogServiceGetLog:
    """Tests for get_log method."""

    def test_get_log_found(self):
        """Test get_log returns log."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()
        mock_log.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result

        result = RetrievalLogService.get_log(mock_db, 1)
        assert result == mock_log

    def test_get_log_not_found(self):
        """Test get_log returns None when not found."""
        from app.services.retrieval_log_service import RetrievalLogService
        mock_db = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = RetrievalLogService.get_log(mock_db, 999)
        assert result is None


class TestRetrievalLogServiceListLogs:
    """Tests for list_logs method."""

    def test_list_logs_success(self):
        """Test list_logs returns logs."""
        from app.services.retrieval_log_service import RetrievalLogService
        mock_db = MagicMock()
        mock_logs = [MagicMock(id=1), MagicMock(id=2)]

        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_db.execute.return_value = mock_result

        # Need to set up execute to return different results for count and data queries
        mock_db.execute.side_effect = [
            mock_result,  # count query
            MagicMock(scalars=MagicMock(all=MagicMock(return_value=mock_logs)))  # data query
        ]

        result, total = RetrievalLogService.list_logs(mock_db, knowledge_base_id=1)
        assert total == 2


class TestRetrievalLogServiceAddFeedback:
    """Tests for add_feedback method."""

    def test_add_feedback_success(self):
        """Test add_feedback success."""
        from app.services.retrieval_log_service import RetrievalLogService
        mock_db = MagicMock()
        mock_log = MagicMock()
        mock_log.id = 1

        mock_feedback = MagicMock()
        mock_feedback.id = 1

        with patch.object(RetrievalLogService, 'get_log', return_value=mock_log):
            with patch('app.services.retrieval_log_service.RetrievalFeedback') as MockFeedback:
                MockFeedback.return_value = mock_feedback

                result, err = RetrievalLogService.add_feedback(
                    db=mock_db,
                    retrieval_log_id=1,
                    user_id=1,
                    feedback_type="helpful",
                    rating=5
                )

                assert err is None
                assert result == mock_feedback

    def test_add_feedback_log_not_found(self):
        """Test add_feedback when log not found."""
        from app.services.retrieval_log_service import RetrievalLogService
        mock_db = MagicMock()

        with patch.object(RetrievalLogService, 'get_log', return_value=None):
            result, err = RetrievalLogService.add_feedback(
                db=mock_db,
                retrieval_log_id=999,
                user_id=1,
                feedback_type="helpful"
            )

            assert result is None
            assert "检索日志不存在" in err

    def test_add_feedback_invalid_type(self):
        """Test add_feedback with invalid type."""
        from app.services.retrieval_log_service import RetrievalLogService
        mock_db = MagicMock()
        mock_log = MagicMock()
        mock_log.id = 1

        with patch.object(RetrievalLogService, 'get_log', return_value=mock_log):
            result, err = RetrievalLogService.add_feedback(
                db=mock_db,
                retrieval_log_id=1,
                user_id=1,
                feedback_type="invalid_type"
            )

            assert result is None
            assert "无效的反馈类型" in err
