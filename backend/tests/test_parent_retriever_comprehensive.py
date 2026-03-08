"""Comprehensive unit tests for parent_retriever.py

Tests cover:
- RetrievalResult dataclass
- ParentRetriever class methods
- All three modes: off, physical, dynamic
- Dynamic expansion functionality
- Physical parent document expansion
- Deduplication logic
- Edge cases and error handling

Author: Test Suite
Date: 2026-03-03
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.rag.parent_retriever import ParentRetriever, RetrievalResult


# ========== RetrievalResult Dataclass Tests ==========


def test_retrieval_result_creation():
    """Test creating RetrievalResult with all required fields."""
    result = RetrievalResult(
        id="123",
        document_id=456,
        knowledge_base_id=789,
        chunk_index=0,
        content="Test content",
        section_title="Section 1",
        metadata={"key": "value"},
        score=0.95,
    )
    assert result.id == "123"
    assert result.document_id == 456
    assert result.knowledge_base_id == 789
    assert result.chunk_index == 0
    assert result.content == "Test content"
    assert result.section_title == "Section 1"
    assert result.metadata == {"key": "value"}
    assert result.score == 0.95
    assert result.is_parent is False


def test_retrieval_result_with_is_parent():
    """Test creating RetrievalResult with is_parent=True."""
    result = RetrievalResult(
        id="123",
        document_id=456,
        knowledge_base_id=789,
        chunk_index=0,
        content="Parent content",
        section_title="Parent Section",
        metadata={},
        score=0.0,
        is_parent=True,
    )
    assert result.is_parent is True
    assert result.score == 0.0


def test_retrieval_result_with_none_section_title():
    """Test creating RetrievalResult with None section_title."""
    result = RetrievalResult(
        id="123",
        document_id=456,
        knowledge_base_id=789,
        chunk_index=0,
        content="Content without section",
        section_title=None,
        metadata={},
        score=0.85,
    )
    assert result.section_title is None


# ========== ParentRetriever: off Mode Tests ==========


@pytest.mark.asyncio
async def test_retrieve_mode_off_returns_original():
    """Test off mode returns original hits without modification."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Hit 1",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]
    result = await retriever.retrieve(hits, mode="off")
    assert result == hits
    assert len(result) == 1


@pytest.mark.asyncio
async def test_retrieve_mode_off_with_empty_hits():
    """Test off mode with empty hits list."""
    retriever = ParentRetriever()
    hits: list[RetrievalResult] = []
    result = await retriever.retrieve(hits, mode="off")
    assert result == []
    assert len(result) == 0


@pytest.mark.asyncio
async def test_retrieve_mode_off_with_multiple_hits():
    """Test off mode preserves all original hits."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id=str(i),
            document_id=i * 100,
            knowledge_base_id=1,
            chunk_index=i,
            content=f"Hit {i}",
            section_title=None,
            metadata={},
            score=0.9 - i * 0.1,
        )
        for i in range(5)
    ]
    result = await retriever.retrieve(hits, mode="off")
    assert len(result) == 5
    assert all(original == returned for original, returned in zip(hits, result))


# ========== ParentRetriever: physical Mode Tests ==========


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_empty_hits(mock_session_local):
    """Test physical expansion with empty hits list."""
    retriever = ParentRetriever()
    hits: list[RetrievalResult] = []
    result = await retriever._physical_expand(hits)
    assert result == []
    mock_session_local.assert_not_called()


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_no_parent_chunk_id(mock_session_local):
    """Test physical expansion when hits have no parent_chunk_id metadata."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Child without parent",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]
    result = await retriever._physical_expand(hits)
    assert result == hits
    mock_session_local.assert_not_called()


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_with_parent_chunks(mock_session_local):
    """Test physical expansion retrieves parent chunks correctly."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="child1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Child content",
            section_title=None,
            metadata={"parent_chunk_id": "parent1"},
            score=0.9,
        ),
        RetrievalResult(
            id="child2",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=1,
            content="Child content 2",
            section_title=None,
            metadata={"parent_chunk_id": "parent2"},
            score=0.85,
        ),
    ]

    # Mock database response
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        ("parent1", 100, 1, 0, "Parent content 1", "Section 1", {}, True),
        ("parent2", 100, 1, 0, "Parent content 2", "Section 2", {"key": "val"}, True),
    ]

    result = await retriever._physical_expand(hits)
    assert len(result) == 2
    assert all(r.is_parent for r in result)
    assert result[0].id == "parent1"
    assert result[1].id == "parent2"
    assert result[0].content == "Parent content 1"
    assert result[1].content == "Parent content 2"


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_deduplication(mock_session_local):
    """Test physical expansion deduplicates parents when multiple children map to same parent."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id=f"child{i}",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=i,
            content=f"Child {i}",
            section_title=None,
            metadata={"parent_chunk_id": "same_parent"},
            score=0.9 - i * 0.1,
        )
        for i in range(3)
    ]

    # Mock database returns single parent
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        ("same_parent", 100, 1, 0, "Shared parent content", "Shared Section", {}, True)
    ]

    result = await retriever._physical_expand(hits)
    assert len(result) == 1  # Only one parent despite 3 children
    assert result[0].id == "same_parent"
    assert result[0].is_parent is True


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_preserves_order(mock_session_local):
    """Test physical expansion preserves the order of original hits."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="child1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Child 1",
            section_title=None,
            metadata={"parent_chunk_id": "parent3"},
            score=0.9,
        ),
        RetrievalResult(
            id="child2",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=1,
            content="Child 2",
            section_title=None,
            metadata={"parent_chunk_id": "parent1"},
            score=0.85,
        ),
        RetrievalResult(
            id="child3",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=2,
            content="Child 3",
            section_title=None,
            metadata={"parent_chunk_id": "parent2"},
            score=0.8,
        ),
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        ("parent1", 100, 1, 0, "Parent 1", "Section 1", {}, True),
        ("parent2", 100, 1, 0, "Parent 2", "Section 2", {}, True),
        ("parent3", 100, 1, 0, "Parent 3", "Section 3", {}, True),
    ]

    result = await retriever._physical_expand(hits)
    assert len(result) == 3
    assert result[0].id == "parent3"
    assert result[1].id == "parent1"
    assert result[2].id == "parent2"


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_no_parents_found(mock_session_local):
    """Test physical expansion falls back to hits when no parents found."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="child1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Child content",
            section_title=None,
            metadata={"parent_chunk_id": "nonexistent_parent"},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = []

    result = await retriever._physical_expand(hits)
    assert result == hits  # Falls back to original hits


@pytest.mark.asyncio
async def test_retrieve_mode_physical():
    """Test retrieve method with physical mode."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Content",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    with patch.object(retriever, "_physical_expand", new_callable=AsyncMock) as mock_expand:
        mock_expand.return_value = hits
        result = await retriever.retrieve(hits, mode="physical")
        mock_expand.assert_called_once_with(hits)
        assert result == hits


# ========== ParentRetriever: dynamic Mode Tests ==========


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_empty_hits(mock_session_local):
    """Test dynamic expansion with empty hits list."""
    retriever = ParentRetriever()
    hits: list[RetrievalResult] = []
    result = await retriever._dynamic_expand(hits, expand_n=2)
    assert result == []
    mock_session_local.assert_not_called()


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_no_document_id(mock_session_local):
    """Test dynamic expansion when hits lack document_id."""
    retriever = ParentRetriever()
    # Create hit without document_id attribute using MagicMock
    hit = MagicMock()
    hit.id = "1"
    hit.content = "Content"
    hit.score = 0.9
    delattr(hit, "document_id")  # Remove document_id attribute
    hits = [hit]

    result = await retriever._dynamic_expand(hits, expand_n=2)
    # Should return original hit as-is
    assert len(result) == 1
    mock_session_local.assert_not_called()


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_no_chunk_index(mock_session_local):
    """Test dynamic expansion when hits lack chunk_index attribute."""
    retriever = ParentRetriever()
    # Create hit without chunk_index attribute
    hit = MagicMock()
    hit.id = "1"
    hit.document_id = 100
    hit.content = "Content"
    hit.score = 0.9
    delattr(hit, "chunk_index")  # Remove chunk_index attribute
    hits = [hit]

    result = await retriever._dynamic_expand(hits, expand_n=2)
    # Should return original hit as-is, but may still query DB
    assert len(result) == 1
    # When chunk_index is missing, DB query happens but hit is returned
    assert result[0].id == "1"


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_expands_adjacent_chunks(mock_session_local):
    """Test dynamic expansion includes adjacent chunks."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk5",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=5,
            content="Middle chunk",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    # Mock 10 chunks, hitting at index 5, expand_n=2 -> should return indices 3,4,5,6,7
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=2)
    assert len(result) == 5  # 2 before + 1 hit + 2 after
    assert result[0].chunk_index == 3
    assert result[1].chunk_index == 4
    assert result[2].chunk_index == 5
    assert result[3].chunk_index == 6
    assert result[4].chunk_index == 7


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_boundary_start(mock_session_local):
    """Test dynamic expansion respects start boundary."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=1,
            content="Early chunk",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=3)
    # chunk_index=1, expand_n=3: range(0, 5) -> indices 0,1,2,3,4
    assert len(result) == 5
    assert result[0].chunk_index == 0
    assert result[1].chunk_index == 1


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_boundary_end(mock_session_local):
    """Test dynamic expansion respects end boundary."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk9",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=9,
            content="Late chunk",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=3)
    assert len(result) == 4  # chunk 6,7,8,9 (can't exceed length)
    assert result[-1].chunk_index == 9
    assert result[-2].chunk_index == 8


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_multiple_hits_same_document(mock_session_local):
    """Test dynamic expansion with multiple hits in same document."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk2",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=2,
            content="First hit",
            section_title=None,
            metadata={},
            score=0.9,
        ),
        RetrievalResult(
            id="chunk7",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=7,
            content="Second hit",
            section_title=None,
            metadata={},
            score=0.85,
        ),
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=1)
    # First hit: chunks 1,2,3; Second hit: chunks 6,7,8
    assert len(result) == 6


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_multiple_documents(mock_session_local):
    """Test dynamic expansion with hits from different documents."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="doc1_chunk2",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=2,
            content="Doc 1 hit",
            section_title=None,
            metadata={},
            score=0.9,
        ),
        RetrievalResult(
            id="doc2_chunk3",
            document_id=200,
            knowledge_base_id=1,
            chunk_index=3,
            content="Doc 2 hit",
            section_title=None,
            metadata={},
            score=0.85,
        ),
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"doc1_chunk{i}", 100, 1, i, f"Doc1 content {i}", None, {}, False)
        for i in range(5)
    ] + [
        (f"doc2_chunk{i}", 200, 1, i, f"Doc2 content {i}", None, {}, False)
        for i in range(5)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=1)
    # Doc1: chunks 1,2,3; Doc2: chunks 2,3,4
    assert len(result) == 6
    doc_ids = {r.document_id for r in result}
    assert doc_ids == {100, 200}


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_custom_expand_n(mock_session_local):
    """Test dynamic expand with custom expand_n parameter."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk5",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=5,
            content="Middle chunk",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=4)
    # expand_n=4: chunks 1,2,3,4,5,6,7,8,9
    assert len(result) == 9


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_preserves_score(mock_session_local):
    """Test dynamic expansion preserves original hit score."""
    retriever = ParentRetriever()
    original_score = 0.87
    hits = [
        RetrievalResult(
            id="chunk5",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=5,
            content="Middle chunk",
            section_title=None,
            metadata={},
            score=original_score,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=1)
    assert all(r.score == original_score for r in result)


@pytest.mark.asyncio
async def test_retrieve_mode_dynamic_default():
    """Test retrieve method with dynamic mode (default)."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Content",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    with patch.object(retriever, "_dynamic_expand", new_callable=AsyncMock) as mock_expand:
        mock_expand.return_value = hits
        result = await retriever.retrieve(hits)  # Default mode is "dynamic"
        mock_expand.assert_called_once_with(hits, 2)  # Default expand_n is 2
        assert result == hits


@pytest.mark.asyncio
async def test_retrieve_mode_dynamic_custom_expand_n():
    """Test retrieve method with dynamic mode and custom expand_n."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Content",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    with patch.object(retriever, "_dynamic_expand", new_callable=AsyncMock) as mock_expand:
        mock_expand.return_value = hits
        result = await retriever.retrieve(hits, mode="dynamic", dynamic_expand_n=5)
        mock_expand.assert_called_once_with(hits, 5)
        assert result == hits


# ========== ParentRetriever: Integration Mode Tests ==========


@pytest.mark.asyncio
async def test_retrieve_invalid_mode():
    """Test retrieve with invalid mode falls back to original."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Content",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    result = await retriever.retrieve(hits, mode="invalid")
    assert result == hits


# ========== ParentRetriever: Edge Cases and Error Handling Tests ==========


@pytest.mark.asyncio
async def test_physical_expand_with_none_metadata():
    """Test physical expansion with None metadata raises AttributeError."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Content",
            section_title=None,
            metadata=None,  # None metadata - code doesn't handle this
            score=0.9,
        )
    ]

    # The actual implementation doesn't handle None metadata and will raise AttributeError
    with pytest.raises(AttributeError):
        await retriever._physical_expand(hits)


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_mixed_parent_chunks(mock_session_local):
    """Test physical expansion with some chunks having parent and some not.

    Current implementation: returns only parent chunks that were found,
    not mixing parents with original child chunks.
    """
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="child1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="With parent",
            section_title=None,
            metadata={"parent_chunk_id": "parent1"},
            score=0.9,
        ),
        RetrievalResult(
            id="child2",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=1,
            content="Without parent",
            section_title=None,
            metadata={},
            score=0.85,
        ),
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        ("parent1", 100, 1, 0, "Parent content", "Section", {}, True)
    ]

    result = await retriever._physical_expand(hits)
    # Current behavior: returns only the parent chunks found
    # Since final_results is not empty (has parent1), returns final_results
    assert len(result) == 1
    assert result[0].id == "parent1"


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_hit_not_in_document(mock_session_local):
    """Test dynamic expansion when hit's chunk_index not found in document."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk99",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=99,  # This chunk doesn't exist
            content="Non-existent chunk",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=1)
    # Should return original hit as-is
    assert len(result) == 1
    assert result[0].chunk_index == 99


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_document_id_not_in_chunks(mock_session_local):
    """Test dynamic expansion when document_id not in doc_chunks.

    This happens when database returns chunks but not for the specific document_id.
    """
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk5",
            document_id=999,  # Different document_id
            knowledge_base_id=1,
            chunk_index=5,
            content="Content",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    # Return chunks for document_id 100, not 999
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=1)
    # Should return original hit as-is since doc_id 999 not in doc_chunks
    assert len(result) == 1
    assert result[0].document_id == 999


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_with_empty_parent_ids(mock_session_local):
    """Test physical expansion when parent_chunk_id values are empty strings."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="child1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Content",
            section_title=None,
            metadata={"parent_chunk_id": ""},  # Empty string
            score=0.9,
        ),
    ]

    result = await retriever._physical_expand(hits)
    # Empty strings are falsy, should return original hits
    assert result == hits


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_with_section_titles(mock_session_local):
    """Test dynamic expansion preserves section titles."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk5",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=5,
            content="Content",
            section_title="Main Section",
            metadata={},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", f"Section {i}", {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=1)
    assert all(r.section_title is not None for r in result)
    # chunk_index=5, expand_n=1: range(4, 7) -> indices 4, 5, 6
    # result[0] = chunk 4, result[1] = chunk 5, result[2] = chunk 6
    assert len(result) == 3
    assert result[1].section_title == "Section 5"  # The original hit (middle)
    assert result[0].section_title == "Section 4"
    assert result[2].section_title == "Section 6"


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_parent_with_metadata(mock_session_local):
    """Test physical expansion preserves parent metadata."""
    retriever = ParentRetriever()
    parent_metadata = {"source": "pdf", "page": 1, "author": "Test"}
    hits = [
        RetrievalResult(
            id="child1",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=0,
            content="Child content",
            section_title=None,
            metadata={"parent_chunk_id": "parent1"},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        ("parent1", 100, 1, 0, "Parent content", "Section", parent_metadata, True)
    ]

    result = await retriever._physical_expand(hits)
    assert len(result) == 1
    assert result[0].metadata == parent_metadata


# ========== Performance and Scale Tests ==========


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_physical_expand_large_dataset(mock_session_local):
    """Test physical expansion handles large number of hits efficiently."""
    retriever = ParentRetriever()
    # Create 100 hits with 50 unique parents (deduplication test)
    hits = []
    parent_map = {}
    for i in range(100):
        parent_id = f"parent{i % 50}"
        hits.append(
            RetrievalResult(
                id=f"child{i}",
                document_id=100,
                knowledge_base_id=1,
                chunk_index=i,
                content=f"Child {i}",
                section_title=None,
                metadata={"parent_chunk_id": parent_id},
                score=0.9 - i * 0.001,
            )
        )
        if parent_id not in parent_map:
            parent_map[parent_id] = True

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    # Mock database returns 50 unique parents
    mock_db.execute.return_value.all.return_value = [
        (f"parent{i}", 100, 1, 0, f"Parent {i}", "Section", {}, True)
        for i in range(50)
    ]

    result = await retriever._physical_expand(hits)
    # Should deduplicate to 50 unique parents
    assert len(result) == 50
    assert all(r.is_parent for r in result)


@pytest.mark.asyncio
@patch("app.rag.parent_retriever.SessionLocal")
async def test_dynamic_expand_expand_n_zero(mock_session_local):
    """Test dynamic expansion with expand_n=0 returns only the hit."""
    retriever = ParentRetriever()
    hits = [
        RetrievalResult(
            id="chunk5",
            document_id=100,
            knowledge_base_id=1,
            chunk_index=5,
            content="Content",
            section_title=None,
            metadata={},
            score=0.9,
        )
    ]

    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.execute.return_value.all.return_value = [
        (f"chunk{i}", 100, 1, i, f"Content {i}", None, {}, False)
        for i in range(10)
    ]

    result = await retriever._dynamic_expand(hits, expand_n=0)
    # Should only return the exact hit chunk
    assert len(result) == 1
    assert result[0].chunk_index == 5
