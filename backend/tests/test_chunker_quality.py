"""Phase 2.2 chunker quality tests."""

from app.rag import TextChunker


def test_chunker_empty_and_short() -> None:
    """空文本返回空列表；短于 chunk_size 的文本返回单块。"""
    c = TextChunker(chunk_size=800, chunk_overlap=100)
    assert c.chunk("") == []
    assert c.chunk("   \n  ") == []
    assert c.chunk("短段落") == ["短段落"]
    assert c.chunk("一行内容") == ["一行内容"]


def test_chunker_overlap_coverage() -> None:
    """相邻块 overlap 正确，整体覆盖原文。"""
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = chunker.chunk(text)
    assert len(chunks) >= 3
    assert chunks[0] == "abcdefghij"
    # step = 10 - 2 = 8, so next start at 8: "ijklmnopqr" etc.
    assert chunks[1].startswith("ijkl")
    # All chars should appear in at least one chunk (no gap)
    merged = set()
    for ch in text:
        for block in chunks:
            if ch in block:
                merged.add(ch)
                break
    assert merged == set(text)


def test_chunker_table_like_text() -> None:
    """含表格/代码样式的纯文本分块不报错，块数合理。"""
    c = TextChunker(chunk_size=800, chunk_overlap=100)
    table = "列A\t列B\n1\t2\n3\t4\n"
    long_table = table * 120  # ~1200 chars
    chunks = c.chunk(long_table)
    assert len(chunks) >= 2
    for i, block in enumerate(chunks[:-1]):
        assert len(block) <= 800, f"block {i} length {len(block)}"
    # 总字符覆盖不少于原文（考虑 overlap 重复）
    total = sum(len(b) for b in chunks)
    assert total >= len(long_table) - 100 * (len(chunks) - 1)


def test_chunker_long_text() -> None:
    """长文本分块稳定，块数约在预期范围。"""
    c = TextChunker(chunk_size=800, chunk_overlap=100)
    step = 700
    text = "中" * 10000
    chunks = c.chunk(text)
    expected_min = (10000 - 800) // step + 1
    assert len(chunks) >= expected_min
    for block in chunks[:-1]:
        assert len(block) <= 800
    assert sum(len(b) for b in chunks) >= 10000 - 100 * (len(chunks) - 1)
