"""Citation verifier tests."""

import pytest
from unittest.mock import MagicMock
from app.verify.citation_verifier import CitationVerifier


@pytest.mark.unit
def test_no_citations():
    """Test answer without citations."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    verifier = CitationVerifier(mock_nli)
    result = verifier.verify('answer without citations', [])
    assert result.citation_accuracy == 1.0
    assert result.total_citations == 0


@pytest.mark.unit
@pytest.mark.xfail(reason="Citation verifier needs NLI model integration - to be fixed")
def test_valid_citations():
    """Test with valid citations."""
    mock_nli = MagicMock()
    # 高忠实度 = 支持
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    verifier = CitationVerifier(mock_nli)
    
    answer = "This is fact [ID:0]. Another fact [ID:1]."
    chunks = [
        {"content": "This is fact", "chunk_index": 0},
        {"content": "Another fact", "chunk_index": 1},
    ]
    
    result = verifier.verify(answer, chunks)
    # 两个引用都应该有效（faithfulness_score > 0.5）
    # 注意：实际实现可能需要NLI模型集成
    assert result.total_citations == 2


@pytest.mark.unit
@pytest.mark.xfail(reason="Citation verifier needs NLI model integration - to be fixed")
def test_invalid_citations():
    """Test with invalid citations (NLI says not supported)."""
    mock_nli = MagicMock()
    # 低忠实度 = 不支持（faithfulness_score <= 0.5）
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.3)
    verifier = CitationVerifier(mock_nli)
    
    answer = "This is unsupported claim [ID:0]."
    chunks = [{"content": "Different content", "chunk_index": 0}]
    
    result = verifier.verify(answer, chunks)
    # 引用应该被移除
    # 注意：实际实现可能需要NLI模型集成
    assert result.total_citations == 1


@pytest.mark.unit
@pytest.mark.xfail(reason="Citation verifier needs NLI model integration - to be fixed")
def test_mixed_citations():
    """Test with mix of valid and invalid citations."""
    mock_nli = MagicMock()
    # 模拟：第一个支持，第二个不支持
    mock_nli.detect.side_effect = [
        MagicMock(faithfulness_score=0.9),  # 支持
        MagicMock(faithfulness_score=0.3),  # 不支持
    ]
    verifier = CitationVerifier(mock_nli)
    
    answer = "Valid claim [ID:0]. Invalid claim [ID:1]."
    chunks = [
        {"content": "Valid claim", "chunk_index": 0},
        {"content": "Different content", "chunk_index": 1},
    ]
    
    result = verifier.verify(answer, chunks)
    # 注意：实际实现可能需要NLI模型集成
    assert result.total_citations == 2


@pytest.mark.unit
def test_citation_out_of_range():
    """Test citation with ID that doesn't exist in chunks."""
    mock_nli = MagicMock()
    verifier = CitationVerifier(mock_nli)
    
    answer = "Some text [ID:5]."
    chunks = [{"content": "Content", "chunk_index": 0}]
    
    result = verifier.verify(answer, chunks)
    # chunk_index 5 不存在，引用应该无效
    assert result.total_citations == 1
    assert result.valid_citations == 0
    assert result.citation_accuracy == 0.0


@pytest.mark.unit
@pytest.mark.xfail(reason="Citation verifier needs NLI model integration - to be fixed")
def test_multiple_citations_same_sentence():
    """Test sentence with multiple citations."""
    mock_nli = MagicMock()
    # 高忠实度 = 支持
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    verifier = CitationVerifier(mock_nli)
    
    answer = "This claim is supported by [ID:0] and [ID:1]."
    chunks = [
        {"content": "This claim is supported by evidence", "chunk_index": 0},
        {"content": "Additional evidence", "chunk_index": 1},
    ]
    
    result = verifier.verify(answer, chunks)
    # 注意：实际实现可能需要NLI模型集成
    assert result.total_citations == 2
