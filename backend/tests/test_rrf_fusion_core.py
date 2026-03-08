"""
Tests for RRF (Reciprocal Rank Fusion) core functionality.

Tests for:
- RRFResult creation
- RRFFusion initialization
- fuse() method
- fuse_dict() method

Author: C2
Date: 2026-03-04
Task: V2.0 Test Coverage Improvement
"""

import pytest


class TestRRFResult:
    """Tests for RRFResult dataclass."""

    def test_rrf_result_creation(self):
        """Test RRFResult creation."""
        from app.rag.rrf_fusion import RRFResult

        result = RRFResult(
            id="chunk_1",
            document_id=1,
            knowledge_base_id=1,
            chunk_index=0,
            content="测试内容",
            section_title="测试章节",
            metadata={},
            rrf_score=0.5,
            original_scores={"vector": 0.95, "bm25": 0.85}
        )

        assert result.id == "chunk_1"
        assert result.document_id == 1
        assert result.knowledge_base_id == 1
        assert result.chunk_index == 0
        assert result.content == "测试内容"
        assert result.section_title == "测试章节"
        assert result.metadata == {}
        assert result.rrf_score == 0.5
        assert result.original_scores == {"vector": 0.95, "bm25": 0.85}


class TestRRFFusion:
    """Tests for RRFFusion class."""

    def test_init_default_k(self):
        """Test RRFFusion initialization with default k."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion()
        assert fusion.k == 60  # Default value

    def test_init_custom_k(self):
        """Test RRFFusion initialization with custom k."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=100)
        assert fusion.k == 100

    def test_init_negative_k(self):
        """Test RRFFusion initialization with negative k."""
        from app.rag.rrf_fusion import RRFFusion

        with pytest.raises(ValueError, match="k must be positive"):
            RRFFusion(k=-10)

    def test_init_zero_k(self):
        """Test RRFFusion initialization with zero k."""
        from app.rag.rrf_fusion import RRFFusion

        with pytest.raises(ValueError, match="k must be positive"):
            RRFFusion(k=0)

    def test_init_small_k(self):
        """Test RRFFusion initialization with small k."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=10)
        assert fusion.k == 10

    def test_init_large_k(self):
        """Test RRFFusion initialization with large k."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=100)
        assert fusion.k == 100

    def test_fuse_empty_results(self):
        """Test fuse with empty results."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion()
        results = fusion.fuse([], [], top_k=10)

        assert results == []

    def test_fuse_single_source(self):
        """Test fuse with single source."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [
                {"id": "chunk_1", "content": "内容1", "score": 0.95},
                {"id": "chunk_2", "content": "内容2", "score": 0.85},
            ]
        ]
        source_names = ["vector"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        assert len(results) == 2
        assert results[0].id == "chunk_1"
        assert results[1].id == "chunk_2"

    def test_fuse_multiple_sources(self):
        """Test fuse with multiple sources."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [  # vector source
                {"id": "chunk_1", "content": "内容1", "score": 0.95},
                {"id": "chunk_2", "content": "内容2", "score": 0.85},
            ],
            [  # bm25 source
                {"id": "chunk_2", "content": "内容2", "bm25_score": 0.90},
                {"id": "chunk_3", "content": "内容3", "bm25_score": 0.80},
            ]
        ]
        source_names = ["vector", "bm25"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        # chunk_1: only in vector (rank 1) -> rrf = 1/(60+1) = 0.0164
        # chunk_2: in both (rank 2 in vector, rank 1 in bm25) -> rrf = 1/(60+2) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323
        # chunk_3: only in bm25 (rank 2) -> rrf = 1/(60+2) = 0.0159
        # chunk_2 should be first (highest RRF score)
        assert len(results) == 3
        assert results[0].id == "chunk_2"  # Highest RRF score
        assert results[1].id == "chunk_1"
        assert results[2].id == "chunk_3"

    def test_fuse_different_score_keys(self):
        """Test fuse with different score keys (score, bm25_score, distance)."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [{"id": "chunk_1", "content": "内容1", "score": 0.95}],
            [{"id": "chunk_1", "content": "内容1", "bm25_score": 0.90}],
            [{"id": "chunk_1", "content": "内容1", "distance": 0.1}],
        ]
        source_names = ["vector", "bm25", "other"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        assert len(results) == 1
        assert results[0].id == "chunk_1"
        # Should preserve original scores from all sources
        assert "vector" in results[0].original_scores
        assert "bm25" in results[0].original_scores
        assert "other" in results[0].original_scores

    def test_fuse_missing_score(self):
        """Test fuse when some results have no score."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [{"id": "chunk_1", "content": "内容1", "score": 0.95}],
            [{"id": "chunk_1", "content": "内容1"}],  # No score
        ]
        source_names = ["vector", "bm25"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        assert len(results) == 1
        assert results[0].id == "chunk_1"
        # Missing score should default to 0.0
        assert 0.0 in results[0].original_scores.values()

    def test_fuse_missing_id(self):
        """Test fuse when some results have no id."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [{"id": "chunk_1", "content": "内容1", "score": 0.95}],
            [{"content": "内容2", "score": 0.85}],  # No id
        ]
        source_names = ["vector", "bm25"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        # Results without id should be skipped
        assert len(results) == 1
        assert results[0].id == "chunk_1"

    def test_fuse_chunk_id_fallback(self):
        """Test fuse using chunk_id when id is missing."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [{"chunk_id": "chunk_1", "content": "内容1", "score": 0.95}],
            [{"chunk_id": "chunk_1", "content": "内容1", "bm25_score": 0.90}],
        ]
        source_names = ["vector", "bm25"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        assert len(results) == 1
        assert results[0].id == "chunk_1"

    def test_fuse_preserves_order_by_rrf_score(self):
        """Test that fuse orders results by RRF score descending."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=10)
        results_list = [
            [  # High ranks in this source -> lower RRF
                {"id": "chunk_1", "score": 0.9},
                {"id": "chunk_2", "score": 0.8},
                {"id": "chunk_3", "score": 0.7},
            ]
        ]
        source_names = ["vector"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        # RRF formula: 1/(k+rank)
        # chunk_1: rank 1 -> 1/(10+1) = 0.0909
        # chunk_2: rank 2 -> 1/(10+2) = 0.0833
        # chunk_3: rank 3 -> 1/(10+3) = 0.0769
        # Should be ordered by RRF score DESC
        assert results[0].rrf_score > results[1].rrf_score
        assert results[1].rrf_score > results[2].rrf_score

    def test_fuse_respects_top_k(self):
        """Test that fuse respects top_k parameter."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [
                {"id": f"chunk_{i}", "content": f"内容{i}", "score": 1.0 - i * 0.1}
                for i in range(20)
            ]
        ]
        source_names = ["vector"]

        results = fusion.fuse(results_list, source_names, top_k=5)

        assert len(results) == 5

    def test_fuse_mismatched_lengths(self):
        """Test fuse with mismatched results_list and source_names lengths."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [[{"id": "chunk_1"}]]
        source_names = ["vector", "bm25"]  # Too many names

        with pytest.raises(ValueError, match="长度必须相同"):
            fusion.fuse(results_list, source_names, top_k=10)

    def test_fuse_dict(self):
        """Test fuse_dict method."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_dict = {
            "vector": [
                {"id": "chunk_1", "content": "内容1", "score": 0.95},
                {"id": "chunk_2", "content": "内容2", "score": 0.85},
            ],
            "bm25": [
                {"id": "chunk_2", "content": "内容2", "bm25_score": 0.90},
                {"id": "chunk_3", "content": "内容3", "bm25_score": 0.80},
            ]
        }

        results = fusion.fuse_dict(results_dict, top_k=10)

        assert len(results) == 3
        assert results[0].id == "chunk_2"  # Highest RRF score (in both)

    def test_fuse_dict_empty(self):
        """Test fuse_dict with empty dict."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results = fusion.fuse_dict({}, top_k=10)

        assert results == []

    def test_rrf_score_calculation(self):
        """Test RRF score calculation formula."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [{"id": "chunk_1", "score": 0.9}],  # rank 1
        ]
        source_names = ["vector"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        # RRF = 1/(k+rank) = 1/(60+1) ≈ 0.016393
        expected_score = 1.0 / (60 + 1)
        assert abs(results[0].rrf_score - expected_score) < 0.0001

    def test_fuse_preserves_metadata(self):
        """Test that fuse preserves result metadata."""
        from app.rag.rrf_fusion import RRFFusion

        fusion = RRFFusion(k=60)
        results_list = [
            [{
                "id": "chunk_1",
                "content": "内容1",
                "score": 0.95,
                "document_id": 1,
                "knowledge_base_id": 1,
                "chunk_index": 0,
                "section_title": "章节1",
                "metadata": {"key": "value"}
            }]
        ]
        source_names = ["vector"]

        results = fusion.fuse(results_list, source_names, top_k=10)

        assert results[0].document_id == 1
        assert results[0].knowledge_base_id == 1
        assert results[0].chunk_index == 0
        assert results[0].section_title == "章节1"
        assert results[0].metadata == {"key": "value"}
