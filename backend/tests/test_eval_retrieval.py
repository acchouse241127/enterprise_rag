"""Tests for evaluation framework.

Tests verify the retrieval evaluation metrics calculation.
"""
import pytest


def test_calculate_recall_at_k():
    """Test Recall@K calculation."""
    from scripts.eval_retrieval import calculate_recall_at_k

    # All relevant documents retrieved
    retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    expected = ["doc1", "doc3", "doc5"]
    recall = calculate_recall_at_k(retrieved, expected, 5)
    assert recall == 1.0

    # Partial recall
    retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    expected = ["doc1", "doc3", "doc6"]
    recall = calculate_recall_at_k(retrieved, expected, 5)
    assert recall == 2.0 / 3.0

    # No relevant documents retrieved
    retrieved = ["doc7", "doc8", "doc9"]
    expected = ["doc1", "doc2"]
    recall = calculate_recall_at_k(retrieved, expected, 5)
    assert recall == 0.0

    # Empty expected list
    retrieved = ["doc1", "doc2"]
    expected = []
    recall = calculate_recall_at_k(retrieved, expected, 5)
    assert recall == 1.0


def test_calculate_mrr():
    """Test Mean Reciprocal Rank calculation."""
    from scripts.eval_retrieval import calculate_mrr

    # First hit at position 1
    retrieved = ["doc1", "doc2", "doc3"]
    expected = ["doc1"]
    mrr = calculate_mrr(retrieved, expected)
    assert mrr == 1.0 / 1

    # First hit at position 3
    retrieved = ["doc4", "doc5", "doc1", "doc2"]
    expected = ["doc1"]
    mrr = calculate_mrr(retrieved, expected)
    assert mrr == 1.0 / 3

    # No relevant documents
    retrieved = ["doc7", "doc8", "doc9"]
    expected = ["doc1", "doc2"]
    mrr = calculate_mrr(retrieved, expected)
    assert mrr == 0.0

    # Empty expected list
    retrieved = ["doc1", "doc2"]
    expected = []
    mrr = calculate_mrr(retrieved, expected)
    assert mrr == 1.0


def test_recall_at_k_edge_cases():
    """Test Recall@K edge cases."""
    from scripts.eval_retrieval import calculate_recall_at_k

    # K larger than retrieved list
    retrieved = ["doc1", "doc2"]
    expected = ["doc1"]
    recall = calculate_recall_at_k(retrieved, expected, 10)
    assert recall == 1.0

    # K smaller than retrieved list
    retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    expected = ["doc1", "doc4"]
    recall = calculate_recall_at_k(retrieved, expected, 3)
    assert recall == 0.5  # Only doc1 in top 3


def test_mrr_with_multiple_relevant():
    """Test MRR with multiple relevant documents."""
    from scripts.eval_retrieval import calculate_mrr

    # First relevant at position 2
    retrieved = ["doc4", "doc1", "doc2", "doc3"]
    expected = ["doc1", "doc2", "doc3"]
    mrr = calculate_mrr(retrieved, expected)
    assert mrr == 1.0 / 2
