"""Confidence scorer tests."""

import pytest
from unittest.mock import MagicMock
from app.verify.confidence_scorer import ConfidenceScorer, ConfidenceScore


@pytest.mark.unit
def test_confidence_high():
    """Test high confidence score."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=0.8)
    assert result.level == 'high'
    assert result.score >= 0.8
    # 原因字段是中文化后的
    assert '忠实度' in result.reason or 'faithfulness' in result.reason


@pytest.mark.unit
def test_confidence_medium():
    """Test medium confidence score."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.6)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=0.5)
    assert result.level == 'medium'
    assert 0.5 <= result.score < 0.8


@pytest.mark.unit
def test_confidence_low():
    """Test low confidence score."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.2)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=0.1)
    assert result.level == 'low'
    assert result.score < 0.5


@pytest.mark.unit
def test_confidence_zero_retrieval_score():
    """Test with zero retrieval score."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=0.0)
    # 置信度应该主要由忠实度决定（0.7 * 0.9 = 0.63）
    assert 0.6 < result.score < 0.65


@pytest.mark.unit
def test_confidence_high_retrieval_score():
    """Test with perfect retrieval score."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=1.0)
    # 应该接近 0.9（主要是忠实度）
    assert result.score > 0.85


@pytest.mark.unit
def test_confidence_boundaries():
    """Test confidence level boundaries."""
    mock_nli = MagicMock()
    scorer = ConfidenceScorer(mock_nli)
    
    # 测试 high/medium 边界（0.8）
    # score = 0.7 * 0.9 + 0.3 * 0.8 = 0.63 + 0.24 = 0.87 > 0.8
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.9)
    result = scorer.score('a', 'b', retrieval_score=0.8)
    assert result.level == 'high'
    
    # 测试 medium/low 边界（0.5）
    # score = 0.7 * 0.6 + 0.3 * 0.5 = 0.42 + 0.15 = 0.57 >= 0.5
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.6)
    result = scorer.score('a', 'b', retrieval_score=0.5)
    assert result.level == 'medium'


@pytest.mark.unit
def test_confidence_score_components():
    """Test that confidence score combines faithfulness and retrieval."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.7)
    scorer = ConfidenceScorer(mock_nli)
    
    # 使用不同的检索分数测试
    result1 = scorer.score('a', 'b', retrieval_score=0.5)
    result2 = scorer.score('a', 'b', retrieval_score=1.0)
    
    # 高检索分数应该增加总体置信度
    assert result2.score > result1.score


@pytest.mark.unit
def test_confidence_reason_format():
    """Test confidence reason format."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=0.85)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('a', 'b', retrieval_score=0.75)
    
    # reason 应该包含关键信息（支持中文和英文）
    reason_lower = result.reason.lower()
    has_faithfulness = "faithfulness" in reason_lower or "忠实度" in reason_lower
    has_retrieval = "retrieval" in reason_lower or "检索" in reason_lower
    assert has_faithfulness
    assert has_retrieval
    assert "0.85" in result.reason or "0.75" in result.reason


@pytest.mark.unit
def test_confidence_score_range():
    """Test confidence score is always in valid range."""
    mock_nli = MagicMock()
    scorer = ConfidenceScorer(mock_nli)
    
    # 测试各种组合
    test_cases = [
        (0.0, 0.0),
        (1.0, 1.0),
        (0.5, 0.5),
        (0.3, 0.9),
    ]
    
    for faithfulness, retrieval in test_cases:
        mock_nli.detect.return_value = MagicMock(faithfulness_score=faithfulness)
        result = scorer.score('a', 'b', retrieval_score=retrieval)
        # 分数应该在 0-1 范围内
        assert 0.0 <= result.score <= 1.0


@pytest.mark.unit
def test_confidence_empty_answer():
    """Test confidence with empty answer."""
    mock_nli = MagicMock()
    mock_nli.detect.return_value = MagicMock(faithfulness_score=1.0)
    scorer = ConfidenceScorer(mock_nli)
    result = scorer.score('', 'b', retrieval_score=0.5)
    
    # 空答案应该返回高置信度（默认 1.0）
    assert result.score >= 0.8


@pytest.mark.unit
def test_confidence_dataclass_fields():
    """Test ConfidenceScore dataclass fields."""
    score = ConfidenceScore(score=0.85, level='high', reason='Test reason')
    
    assert score.score == 0.85
    assert score.level == 'high'
    assert score.reason == 'Test reason'
