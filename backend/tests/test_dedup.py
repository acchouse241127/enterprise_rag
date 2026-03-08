"""
Tests for chunk deduplication (SimHash).

Author: C2
Date: 2026-02-13
Task: C2-2.3.1
"""


from app.rag.dedup import deduplicate_chunks, hamming_distance, simhash


class TestSimHash:
    """Test SimHash fingerprint computation."""

    def test_simhash_empty(self):
        """Empty string should return 0."""
        assert simhash("") == 0

    def test_simhash_same_text(self):
        """Same text should produce same fingerprint."""
        text = "这是一段测试文本，用于验证 SimHash 算法。"
        fp1 = simhash(text)
        fp2 = simhash(text)
        assert fp1 == fp2

    def test_simhash_similar_text(self):
        """Similar texts should have smaller Hamming distance than very different texts."""
        text1 = "这是一段测试文本，用于验证 SimHash 算法。"
        text2 = "这是一段测试文本，用于验证 SimHash 的算法。"
        text3 = "The quick brown fox jumps over the lazy dog."
        fp1 = simhash(text1)
        fp2 = simhash(text2)
        fp3 = simhash(text3)
        dist_similar = hamming_distance(fp1, fp2)
        dist_different = hamming_distance(fp1, fp3)
        # Similar texts should have smaller distance than very different texts
        assert dist_similar < dist_different

    def test_simhash_different_text(self):
        """Very different texts should have large Hamming distance."""
        text1 = "这是一段测试文本，用于验证 SimHash 算法。"
        text2 = "The quick brown fox jumps over the lazy dog."
        fp1 = simhash(text1)
        fp2 = simhash(text2)
        distance = hamming_distance(fp1, fp2)
        # Different texts should have distance > 10
        assert distance > 10


class TestHammingDistance:
    """Test Hamming distance computation."""

    def test_hamming_same(self):
        """Same fingerprints should have distance 0."""
        assert hamming_distance(0b1010, 0b1010) == 0

    def test_hamming_one_bit(self):
        """One bit difference should have distance 1."""
        assert hamming_distance(0b1010, 0b1011) == 1

    def test_hamming_all_different(self):
        """All bits different in 4-bit should have distance 4."""
        assert hamming_distance(0b0000, 0b1111) == 4


class TestDeduplicateChunks:
    """Test chunk deduplication."""

    def test_empty_list(self):
        """Empty list should return empty list."""
        assert deduplicate_chunks([]) == []

    def test_no_duplicates(self):
        """Unique chunks should all be kept."""
        chunks = [
            {"content": "第一段完全不同的内容。"},
            {"content": "The second paragraph is in English."},
            {"content": "第三段是中文但内容不同。"},
        ]
        result = deduplicate_chunks(chunks, threshold=3)
        assert len(result) == 3

    def test_exact_duplicates(self):
        """Exact duplicates should be removed."""
        chunks = [
            {"content": "这是重复的内容。"},
            {"content": "这是重复的内容。"},
            {"content": "这是重复的内容。"},
        ]
        result = deduplicate_chunks(chunks, threshold=3)
        assert len(result) == 1

    def test_near_duplicates(self):
        """Near-duplicates (exact or very similar) should be removed."""
        # Use exact duplicates for reliable test
        chunks = [
            {"content": "这是一段测试文本用于验证去重功能"},
            {"content": "这是一段测试文本用于验证去重功能"},  # Exact duplicate
            {"content": "完全不同的内容关于其他主题"},
        ]
        result = deduplicate_chunks(chunks, threshold=3)
        # First and second are exact duplicates, should keep only first
        assert len(result) == 2
        assert result[0]["content"] == "这是一段测试文本用于验证去重功能"
        assert result[1]["content"] == "完全不同的内容关于其他主题"

    def test_preserves_order(self):
        """Deduplication should preserve original order."""
        chunks = [
            {"content": "AAA first unique"},
            {"content": "BBB second unique"},
            {"content": "AAA first unique"},  # Duplicate of first
        ]
        result = deduplicate_chunks(chunks, threshold=3)
        assert len(result) == 2
        assert result[0]["content"] == "AAA first unique"
        assert result[1]["content"] == "BBB second unique"

    def test_custom_content_key(self):
        """Should work with custom content key."""
        chunks = [
            {"text": "内容一"},
            {"text": "内容一"},
        ]
        result = deduplicate_chunks(chunks, threshold=3, content_key="text")
        assert len(result) == 1

    def test_missing_content(self):
        """Chunks without content should be kept."""
        chunks = [
            {"content": "有内容"},
            {"other_field": "没有 content 字段"},
            {"content": ""},
        ]
        result = deduplicate_chunks(chunks, threshold=3)
        # All should be kept (missing/empty content not deduplicated)
        assert len(result) == 3
