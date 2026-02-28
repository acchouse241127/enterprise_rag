"""Confidence scorer tests."""

from unittest.mock import MagicMock
from app.verify.confidence_scorer import ConfidenceScorer

def test_confidence_high():
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=0.8)
    assert result.level == 'high'

def test_confidence_medium():
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.6)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=0.5)
    assert result.level == 'medium'

def test_confidence_low():
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.2)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=0.1)
    assert result.level == 'low'
