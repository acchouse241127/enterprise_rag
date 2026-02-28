"""Refusal handler tests."""

from app.verify.refusal import RefusalHandler

def test_refusal_empty_retrieval():
    handler = RefusalHandler()
    result = handler.handle('empty_retrieval')
    assert result.reason == 'empty_retrieval'
    assert '知识库' in result.message
