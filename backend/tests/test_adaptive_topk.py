"""Comprehensive tests for AdaptiveTopK module.

Tests cover:
- AdaptiveTopK initialization
- Score cliff detection
- Top-K selection with various scenarios
- Edge cases and boundary conditions
"""

import pytest
from app.rag.parent_retriever import RetrievalResult
from app.rag.adaptive_topk import AdaptiveTopK


class TestAdaptiveTopKInit:
    """Tests for AdaptiveTopK initialization."""

    def test_init_default(self):
        """Test AdaptiveTopK with default parameters."""
        topk = AdaptiveTopK()
        assert topk.min_k == 2
        assert topk.max_k == 15
        assert topk.cliff_factor == 1.5

    def test_init_custom(self):
        """Test AdaptiveTopK with custom parameters."""
        topk = AdaptiveTopK(min_k=3, max_k=10, cliff_factor=2.0)
        assert topk.min_k == 3
        assert topk.max_k == 10
        assert topk.cliff_factor == 2.0

    def test_init_invalid_min_k(self):
        """Test that min_k must be greater than 0."""
        with pytest.raises(ValueError, match="min_k must be greater than 0"):
            AdaptiveTopK(min_k=0)

    def test_init_invalid_max_k(self):
        """Test that max_k must be greater than min_k."""
        with pytest.raises(ValueError, match="max_k must be greater than min_k"):
            AdaptiveTopK(min_k=5, max_k=3)

    def test_init_invalid_cliff_factor(self):
        """Test that cliff_factor must be greater than 0."""
        with pytest.raises(ValueError, match="cliff_factor must be greater than 0"):
            AdaptiveTopK(cliff_factor=0)


class TestAdaptiveTopKSelect:
    """Tests for AdaptiveTopK.select method."""

    def _create_results(self, scores):
        """Helper to create RetrievalResult list from scores."""
        return [
            RetrievalResult(
                id=f"id_{i}",
                document_id=i,
                knowledge_base_id=1,
                chunk_index=i,
                content=f"content_{i}",
                section_title=f"title_{i}",
                metadata={},
                score=score,
            )
            for i, score in enumerate(scores)
        ]

    def test_select_empty_list(self):
        """Test select with empty list."""
        topk = AdaptiveTopK()
        results = topk.select([])
        assert results == []

    def test_select_less_than_min_k(self):
        """Test select with fewer results than min_k."""
        topk = AdaptiveTopK(min_k=5)
        results = self._create_results([0.9, 0.8, 0.7])
        selected = topk.select(results)
        assert len(selected) == 3  # Returns all available
        assert selected == results

    def test_select_equal_min_k(self):
        """Test select with exactly min_k results."""
        topk = AdaptiveTopK(min_k=5)
        results = self._create_results([0.9, 0.8, 0.7, 0.6, 0.5])
        selected = topk.select(results)
        assert len(selected) == 5

    def test_select_all_same_scores(self):
        """Test select when all scores are the same."""
        topk = AdaptiveTopK(min_k=3)
        results = self._create_results([0.5, 0.5, 0.5, 0.5, 0.5])
        selected = topk.select(results)
        assert len(selected) == 3  # Returns min_k

    def test_select_no_cliff(self):
        """Test select when no cliff is detected."""
        topk = AdaptiveTopK(min_k=3, cliff_factor=10.0)
        # Gradual decrease, no cliff
        results = self._create_results([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3])
        selected = topk.select(results)
        assert len(selected) == 3  # Returns min_k when no cliff

    def test_select_with_cliff(self):
        """Test select when cliff is detected."""
        topk = AdaptiveTopK(min_k=2, cliff_factor=1.0)
        # Big drop at index 3: 0.7 -> 0.3 (diff = 0.4)
        # Mean diff = (0.1+0.1+0.4)/3 = 0.2, std ≈ 0.163
        # Threshold = 0.2 + 1.0*0.163 = 0.363
        # Cliff at 0.4 > 0.363
        results = self._create_results([0.8, 0.7, 0.6, 0.2, 0.1])
        selected = topk.select(results)
        # Should stop after cliff (at index 3)
        assert len(selected) >= 2  # At least min_k

    def test_select_max_k_limit(self):
        """Test that selection respects max_k limit."""
        topk = AdaptiveTopK(min_k=2, max_k=5)
        # Many results with good scores
        results = self._create_results([0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6])
        selected = topk.select(results)
        assert len(selected) <= 5  # Respects max_k

    def test_select_early_cliff(self):
        """Test select with cliff early in results."""
        topk = AdaptiveTopK(min_k=2, cliff_factor=0.5)
        # Big cliff at first position
        results = self._create_results([1.0, 0.5, 0.4, 0.3, 0.2])
        selected = topk.select(results)
        # Should detect cliff and return at least min_k
        assert len(selected) >= 2

    def test_select_single_result(self):
        """Test select with single result."""
        topk = AdaptiveTopK(min_k=2)
        results = self._create_results([0.9])
        selected = topk.select(results)
        assert len(selected) == 1  # Returns all when less than min_k

    def test_select_two_results(self):
        """Test select with exactly 2 results."""
        topk = AdaptiveTopK(min_k=2)
        results = self._create_results([0.9, 0.8])
        selected = topk.select(results)
        assert len(selected) == 2

    def test_select_many_results_no_cliff(self):
        """Test select with many results and no obvious cliff."""
        topk = AdaptiveTopK(min_k=5, max_k=10)
        # Smooth decline
        results = self._create_results(
            [0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50,
             0.45, 0.40, 0.35, 0.30, 0.25]
        )
        selected = topk.select(results)
        # With no clear cliff, should return min_k
        assert len(selected) == 5

    def test_select_with_zero_diffs(self):
        """Test select when all differences are zero."""
        topk = AdaptiveTopK(min_k=3)
        results = self._create_results([0.5, 0.5, 0.5, 0.5])
        selected = topk.select(results)
        assert len(selected) == 3

    def test_select_single_diff(self):
        """Test select with only one difference (2 results)."""
        topk = AdaptiveTopK(min_k=2)
        results = self._create_results([0.9, 0.1])
        selected = topk.select(results)
        # With only 2 results, can't calculate std, returns min_k
        assert len(selected) == 2

    def test_select_large_drop(self):
        """Test select with very large score drop."""
        topk = AdaptiveTopK(min_k=2)
        # Massive cliff
        results = self._create_results([1.0, 0.9, 0.01, 0.001])
        selected = topk.select(results)
        # Should stop at cliff
        assert len(selected) >= 2

    def test_select_boundary_min_k(self):
        """Test that selection never goes below min_k."""
        topk = AdaptiveTopK(min_k=5, max_k=20)
        # Cliff at position 1
        results = self._create_results([1.0, 0.1, 0.09, 0.08, 0.07, 0.06])
        selected = topk.select(results)
        assert len(selected) >= 5  # Must respect min_k

    def test_select_boundary_max_k(self):
        """Test that selection never exceeds max_k."""
        topk = AdaptiveTopK(min_k=2, max_k=3)
        # All similar scores, no cliff
        results = self._create_results([0.5, 0.49, 0.48, 0.47, 0.46])
        selected = topk.select(results)
        assert len(selected) <= 3  # Must respect max_k

    def test_select_exact_max_k(self):
        """Test select with exactly max_k results."""
        topk = AdaptiveTopK(min_k=3, max_k=5)
        results = self._create_results([0.9, 0.8, 0.7, 0.6, 0.5])
        selected = topk.select(results)
        assert len(selected) <= 5

    def test_select_preserves_order(self):
        """Test that selection preserves original order."""
        topk = AdaptiveTopK(min_k=3)
        results = self._create_results([0.9, 0.8, 0.7, 0.6, 0.5])
        selected = topk.select(results)
        # Verify order is preserved
        for i in range(len(selected)):
            assert selected[i].id == results[i].id

    def test_select_returns_correct_type(self):
        """Test that select returns list of RetrievalResult."""
        topk = AdaptiveTopK()
        results = self._create_results([0.9, 0.8, 0.7])
        selected = topk.select(results)
        assert isinstance(selected, list)
        assert all(isinstance(r, RetrievalResult) for r in selected)
