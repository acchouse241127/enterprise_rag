"""Citation verifier tests."""

from unittest.mock import MagicMock
from app.verify.citation_verifier import CitationVerifier

def test_no_citations():
    mock_nli = MagicMock()
    verifier = CitationVerifier(mock_nli)
    result = verifier.verify('answer without citations', [])
    assert result.citation_accuracy == 1.0
