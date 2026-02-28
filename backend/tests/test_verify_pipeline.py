"""Verify pipeline tests."""

from unittest.mock import MagicMock, patch
from app.verify.verify_pipeline import VerifyPipeline, VerificationAction

def test_verify_pass():
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    pipeline = VerifyPipeline(mock_nli)
    result = pipeline.verify('answer', ['context'], retrieval_score=0.8)
    assert result.action == VerificationAction.PASS
