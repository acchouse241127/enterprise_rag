"""NLI hallucination detector tests."""

from unittest.mock import MagicMock, patch
from app.verify.nli_detector import NLIHallucinationDetector as NLIDetector, NLILabel


def test_nli_entailment():
    """Test entailment detection."""
    mock_model = MagicMock()
    mock_model.predict.return_value = "entailment"
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("What is pension?", "Pension is retirement fund.")
        assert result.label == NLILabel.ENTAILMENT
        assert result.faithfulness_score > 0.5


def test_nli_contradiction():
    """Test contradiction detection."""
    mock_model = MagicMock()
    mock_model.predict.return_value = "contradiction"
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("Capital of China?", "New York is in USA.")
        assert result.label == NLILabel.CONTRADICTION
        assert result.faithfulness_score < 0.5


def test_nli_neutral():
    """Test neutral detection."""
    mock_model = MagicMock()
    mock_model.predict.return_value = "neutral"
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("What is RAG?", "RAG is retrieval augmented generation.")
        assert result.label == NLILabel.NEUTRAL
