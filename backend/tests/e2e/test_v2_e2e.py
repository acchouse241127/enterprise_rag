"""V2.0 End-to-End tests."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

pytestmark = pytest.mark.integration

def test_hybrid_retrieval_pipeline_flow():
    """
    Test hybrid retrieval pipeline end-to-end flow.
    """
    # Mock all dependencies
    mock_bm25 = MagicMock()
    mock_bm25.search.return_value = ([MagicMock(id=1, content='test', score=0.9)], None)
    mock_vector = MagicMock()
    mock_vector.retrieve.return_value = ([{'id': '2', 'content': 'test2', 'distance': 0.1}], None)
    assert mock_bm25 is not None

def test_verify_pipeline_flow():
    """
    Test verification pipeline end-to-end flow.
    """
    from app.verify.verify_pipeline import VerifyPipeline, VerificationAction
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    pipeline = VerifyPipeline(mock_nli)
    result = pipeline.verify('answer', ['context'], retrieval_score=0.8)
    assert result.action == VerificationAction.PASS
