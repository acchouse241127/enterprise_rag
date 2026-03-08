# BM25 测试占位符

import pytest

# 初始版本：仅占位，待 chunker 等模块就绪后完善
# BM25 retriever 模块需要与 chunker 集成后才能进行完整测试

pytestmark = pytest.mark.skip(reason="BM25 retriever module not ready - pending chunker integration")


def test_bm25_placeholder():
    """Placeholder test for BM25 retriever."""
    pass
