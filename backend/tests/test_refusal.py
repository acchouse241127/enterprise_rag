"""Refusal handler tests."""

import pytest
from app.verify.refusal import RefusalHandler


@pytest.mark.unit
def test_refusal_empty_retrieval():
    """Test refusal for empty retrieval."""
    handler = RefusalHandler()
    result = handler.handle('empty_retrieval')
    assert result.reason == 'empty_retrieval'
    assert '知识库' in result.message
    assert result.message is not None


@pytest.mark.unit
def test_refusal_low_relevance():
    """Test refusal for low relevance."""
    handler = RefusalHandler()
    result = handler.handle('low_relevance')
    assert result.reason == 'low_relevance'
    assert '关联度较低' in result.message


@pytest.mark.unit
def test_refusal_low_confidence():
    """Test refusal for low confidence."""
    handler = RefusalHandler()
    result = handler.handle('low_confidence')
    assert result.reason == 'low_confidence'
    assert '置信度不足' in result.message


@pytest.mark.unit
def test_refusal_low_faithfulness():
    """Test refusal for low faithfulness."""
    handler = RefusalHandler()
    result = handler.handle('low_faithfulness')
    assert result.reason == 'low_faithfulness'
    assert '不一致' in result.message


@pytest.mark.unit
def test_refusal_unknown_reason():
    """Test refusal for unknown reason."""
    handler = RefusalHandler()
    result = handler.handle('unknown_reason')
    assert result.reason == 'unknown_reason'
    assert '未知原因' in result.message
    assert '请尝试其他问题' in result.message


@pytest.mark.unit
def test_refusal_with_custom_threshold():
    """Test refusal with custom threshold."""
    handler = RefusalHandler()
    result = handler.handle('low_confidence', refusal_threshold=0.4)
    assert result.reason == 'low_confidence'
    assert '0.4' in result.message  # 应该包含自定义阈值


@pytest.mark.unit
def test_refusal_default_message():
    """Test default refusal message exists."""
    handler = RefusalHandler()
    assert handler.DEFAULT_MESSAGE is not None
    assert len(handler.DEFAULT_MESSAGE) > 0
    assert '无法' in handler.DEFAULT_MESSAGE


@pytest.mark.unit
def test_refusal_reason_messages():
    """Test all reason messages are defined."""
    handler = RefusalHandler()
    expected_reasons = [
        'empty_retrieval',
        'low_relevance',
        'low_confidence',
        'low_faithfulness',
    ]
    
    for reason in expected_reasons:
        result = handler.handle(reason)
        assert result.reason == reason
        assert result.message is not None
        assert len(result.message) > 0
