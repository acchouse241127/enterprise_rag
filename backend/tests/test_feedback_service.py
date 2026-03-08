"""Feedback service tests."""

import pytest
from unittest.mock import MagicMock
from app.services.feedback_service import FeedbackService


@pytest.mark.unit
def test_feedback_service_init():
    """Test feedback service initialization."""
    # FeedbackService is a static service, no init needed
    assert FeedbackService is not None


@pytest.mark.unit
def test_submit_feedback_structure():
    """Test submit_feedback method structure."""
    # Test that the method signature exists
    assert hasattr(FeedbackService, 'submit_feedback')
    assert callable(getattr(FeedbackService, 'submit_feedback'))


@pytest.mark.unit
def test_retrieval_feedback_model():
    """Test retrieval feedback model can be imported."""
    from app.models.retrieval_log import RetrievalFeedback
    
    # Test that RetrievalFeedback can be instantiated
    feedback = RetrievalFeedback(
        retrieval_log_id=1,
        user_id=1,
        feedback_type="helpful",
        rating=5,
        reason="Great answer!"
    )
    
    assert feedback.retrieval_log_id == 1
    assert feedback.feedback_type == "helpful"
    assert feedback.rating == 5
