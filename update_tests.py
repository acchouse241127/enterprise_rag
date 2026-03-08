import os

tests = {
    "backend/tests/test_nli_detector.py": '''"""NLI hallucination detector tests."""

from unittest.mock import MagicMock, patch
from app.verify.nli_detector import NLIHallucinationDetector as NLIDetector, NLILabel


def test_nli_entailment():
    mock_model = MagicMock()
    mock_model.predict.return_value = "entailment"
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("Q", "A")
        assert result.label == NLILabel.ENTAILMENT


def test_nli_contradiction():
    mock_model = MagicMock()
    mock_model.predict.return_value = "contradiction"
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("Q", "A")
        assert result.label == NLILabel.CONTRADICTION
''',
}

for path, content in tests.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {path}")
