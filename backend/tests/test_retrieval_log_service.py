"""
Unit tests for RetrievalLogService.

Tests for app/services/retrieval_log_service.py
Author: C2
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestRetrievalLogServiceCreate:
    """Tests for RetrievalLogService.create_log."""

    def test_create_log_basic(self):
        """Test basic log creation."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()
        mock_log.id = 1

        with patch("app.services.retrieval_log_service.RetrievalLog") as MockLog:
            MockLog.return_value = mock_log
            result = RetrievalLogService.create_log(
                db=mock_db,
                knowledge_base_id=1,
                user_id=1,
                query="test query"
            )
            assert result == mock_log
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    def test_create_log_with_all_fields(self):
        """Test log creation with all optional fields."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch("app.services.retrieval_log_service.RetrievalLog") as MockLog:
            MockLog.return_value = mock_log
            result = RetrievalLogService.create_log(
                db=mock_db,
                knowledge_base_id=1,
                user_id=1,
                query="test query",
                chunks_retrieved=10,
                chunks_after_filter=8,
                chunks_after_dedup=6,
                chunks_after_rerank=5,
                top_chunk_score=0.95,
                avg_chunk_score=0.85,
                min_chunk_score=0.75,
                chunk_details=[{"id": 1, "score": 0.95}],
                cited_chunk_ids=[1, 2, 3],
                query_embedding_time_ms=10,
                retrieval_time_ms=50,
                rerank_time_ms=20,
                total_time_ms=100,
                llm_time_ms=500,
                answer_generated=True,
                answer_length=100
            )
            assert result == mock_log

    def test_create_log_with_v2_fields(self):
        """Test log creation with V2.0 quality metrics."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch("app.services.retrieval_log_service.RetrievalLog") as MockLog:
            MockLog.return_value = mock_log
            result = RetrievalLogService.create_log(
                db=mock_db,
                knowledge_base_id=1,
                user_id=1,
                query="test query",
                confidence_score=0.85,
                faithfulness_score=0.90,
                has_hallucination=False,
                retrieval_mode="hybrid",
                refusal_reason=None,
                citation_accuracy=0.95
            )
            assert result == mock_log

    def test_create_log_answer_generated_true(self):
        """Test that answer_generated=True is converted to 1."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch("app.services.retrieval_log_service.RetrievalLog") as MockLog:
            MockLog.return_value = mock_log
            RetrievalLogService.create_log(
                db=mock_db,
                knowledge_base_id=1,
                user_id=1,
                query="test",
                answer_generated=True
            )
            call_kwargs = MockLog.call_args[1]
            assert call_kwargs["answer_generated"] == 1

    def test_create_log_answer_generated_false(self):
        """Test that answer_generated=False is converted to 0."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch("app.services.retrieval_log_service.RetrievalLog") as MockLog:
            MockLog.return_value = mock_log
            RetrievalLogService.create_log(
                db=mock_db,
                knowledge_base_id=1,
                user_id=1,
                query="test",
                answer_generated=False
            )
            call_kwargs = MockLog.call_args[1]
            assert call_kwargs["answer_generated"] == 0

    def test_create_log_has_hallucination_true(self):
        """Test that has_hallucination=True is converted to 1."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch("app.services.retrieval_log_service.RetrievalLog") as MockLog:
            MockLog.return_value = mock_log
            RetrievalLogService.create_log(
                db=mock_db,
                knowledge_base_id=1,
                user_id=1,
                query="test",
                has_hallucination=True
            )
            call_kwargs = MockLog.call_args[1]
            assert call_kwargs["has_hallucination"] == 1

    def test_create_log_has_hallucination_none(self):
        """Test that has_hallucination=None stays as None."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch("app.services.retrieval_log_service.RetrievalLog") as MockLog:
            MockLog.return_value = mock_log
            RetrievalLogService.create_log(
                db=mock_db,
                knowledge_base_id=1,
                user_id=1,
                query="test",
                has_hallucination=None
            )
            call_kwargs = MockLog.call_args[1]
            assert call_kwargs["has_hallucination"] is None


class TestRetrievalLogServiceGet:
    """Tests for RetrievalLogService.get_log."""

    def test_get_log_found(self):
        """Test getting existing log."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_log = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result

        result = RetrievalLogService.get_log(mock_db, 1)
        assert result == mock_log

    def test_get_log_not_found(self):
        """Test getting non-existent log."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = RetrievalLogService.get_log(mock_db, 999)
        assert result is None


class TestRetrievalLogServiceList:
    """Tests for RetrievalLogService.list_logs."""

    def test_list_logs_no_filters(self):
        """Test listing logs without filters."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        # Mock list query
        mock_list_result = MagicMock()
        mock_logs = [MagicMock(), MagicMock()]
        mock_list_result.scalars.return_value.all.return_value = mock_logs

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        logs, total = RetrievalLogService.list_logs(mock_db)
        assert len(logs) == 2
        assert total == 2

    def test_list_logs_with_knowledge_base_filter(self):
        """Test listing logs filtered by knowledge base."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_list_result = MagicMock()
        mock_logs = [MagicMock()]
        mock_list_result.scalars.return_value.all.return_value = mock_logs

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        logs, total = RetrievalLogService.list_logs(mock_db, knowledge_base_id=5)
        assert len(logs) == 1

    def test_list_logs_with_date_filter(self):
        """Test listing logs filtered by date range."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        start = datetime.now() - timedelta(days=7)
        end = datetime.now()
        logs, total = RetrievalLogService.list_logs(
            mock_db, start_date=start, end_date=end
        )
        assert logs == []


class TestRetrievalLogServiceFeedback:
    """Tests for RetrievalLogService.add_feedback."""

    def test_add_feedback_helpful(self):
        """Test adding helpful feedback."""
        from app.services.retrieval_log_service import RetrievalLogService
        from app.models import FeedbackType

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch.object(RetrievalLogService, "get_log", return_value=mock_log):
            with patch("app.services.retrieval_log_service.FeedbackType") as MockFT:
                MockFT.HELPFUL.value = "helpful"
                MockFT.NOT_HELPFUL.value = "not_helpful"

                with patch("app.services.retrieval_log_service.RetrievalFeedback") as MockFeedback:
                    mock_feedback = MagicMock()
                    MockFeedback.return_value = mock_feedback

                    result, err = RetrievalLogService.add_feedback(
                        mock_db, 1, 1, "helpful"
                    )
                    assert result == mock_feedback
                    assert err is None

    def test_add_feedback_invalid_type(self):
        """Test adding feedback with invalid type."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch.object(RetrievalLogService, "get_log", return_value=mock_log):
            with patch("app.services.retrieval_log_service.FeedbackType") as MockFT:
                MockFT.HELPFUL.value = "helpful"
                MockFT.NOT_HELPFUL.value = "not_helpful"

                result, err = RetrievalLogService.add_feedback(
                    mock_db, 1, 1, "invalid_type"
                )
                assert result is None
                assert "无效的反馈类型" in err

    def test_add_feedback_log_not_found(self):
        """Test adding feedback for non-existent log."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()

        with patch.object(RetrievalLogService, "get_log", return_value=None):
            result, err = RetrievalLogService.add_feedback(
                mock_db, 999, 1, "helpful"
            )
            assert result is None
            assert "不存在" in err

    def test_add_feedback_with_rating(self):
        """Test adding feedback with explicit rating."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_log = MagicMock()

        with patch.object(RetrievalLogService, "get_log", return_value=mock_log):
            with patch("app.services.retrieval_log_service.FeedbackType") as MockFT:
                MockFT.HELPFUL.value = "helpful"
                MockFT.NOT_HELPFUL.value = "not_helpful"

                with patch("app.services.retrieval_log_service.RetrievalFeedback") as MockFeedback:
                    mock_feedback = MagicMock()
                    MockFeedback.return_value = mock_feedback

                    result, err = RetrievalLogService.add_feedback(
                        mock_db, 1, 1, "helpful", rating=5
                    )
                    assert result == mock_feedback


class TestRetrievalLogServiceUpdateVerification:
    """Tests for RetrievalLogService.update_verification_metrics."""

    def test_update_verification_metrics_success(self):
        """Test updating verification metrics."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_log = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result

        success, err = RetrievalLogService.update_verification_metrics(
            mock_db, 1,
            confidence_score=0.85,
            faithfulness_score=0.90
        )
        assert success == True
        assert err is None

    def test_update_verification_metrics_log_not_found(self):
        """Test updating metrics for non-existent log."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        success, err = RetrievalLogService.update_verification_metrics(
            mock_db, 999
        )
        assert success == False
        assert "不存在" in err


class TestRetrievalLogServiceMarkAsSample:
    """Tests for RetrievalLogService.mark_as_sample."""

    def test_mark_as_sample_true(self):
        """Test marking feedback as sample."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_feedback = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_feedback
        mock_db.execute.return_value = mock_result

        result, err = RetrievalLogService.mark_as_sample(mock_db, 1, is_sample=True)
        assert result == mock_feedback
        assert err is None

    def test_mark_as_sample_not_found(self):
        """Test marking non-existent feedback."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result, err = RetrievalLogService.mark_as_sample(mock_db, 999)
        assert result is None
        assert "不存在" in err


class TestRetrievalLogServiceStats:
    """Tests for RetrievalLogService.get_stats."""

    def test_get_stats_basic(self):
        """Test getting basic statistics."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()

        # Mock multiple scalar queries
        mock_db.execute.return_value.scalar.return_value = 10

        stats = RetrievalLogService.get_stats(mock_db)
        assert "total_queries" in stats
        assert "helpful_count" in stats
        assert "not_helpful_count" in stats

    def test_get_stats_with_knowledge_base_filter(self):
        """Test getting statistics for specific knowledge base."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 5

        stats = RetrievalLogService.get_stats(mock_db, knowledge_base_id=1)
        assert "total_queries" in stats

    def test_get_stats_zero_queries(self):
        """Test statistics with no queries."""
        from app.services.retrieval_log_service import RetrievalLogService

        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 0

        stats = RetrievalLogService.get_stats(mock_db)
        assert stats["total_queries"] == 0
        assert stats["not_helpful_ratio"] == 0
