"""Tests for self-query retriever.

TDD Phase 2.1: Self-Query Retriever
- LLM-based intent parsing
- Metadata filter extraction
- Query construction with filters
- Reranking integration

Author: C2
Date: 2026-03-03
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestSelfQueryRetriever:
    """Tests for self-query retriever."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        provider = MagicMock()
        provider.generate = MagicMock(return_value=json.dumps({
            "intent": "filter",
            "metadata": {"year": 2024, "document_type": "report"},
            "filter": {"year": {"$eq": 2024}},
            "original_query": "查询2024年的财务报告",
        }))
        return provider

    @pytest.fixture
    def mock_retriever(self):
        """Create mock base retriever."""
        retriever = MagicMock()
        retriever.retrieve = MagicMock(return_value=(
            [{"chunk_id": 1, "content": "test content", "distance": 0.1}],
            None,
        ))
        return retriever

    @pytest.fixture
    def mock_reranker(self):
        """Create mock reranker."""
        reranker = MagicMock()
        reranker.rerank = MagicMock(return_value=[
            {"chunk_id": 1, "content": "test content", "rerank_score": 0.9}
        ])
        return reranker

    @pytest.fixture
    def mock_embedding(self):
        """Create mock embedding service."""
        service = MagicMock()
        service.embed = MagicMock(return_value=[[0.1] * 1024])
        return service

    def test_extract_metadata_success(self, mock_llm, mock_retriever, mock_reranker, mock_embedding):
        """Test successful metadata extraction from query."""
        from app.rag.self_query_retriever import SelfQueryRetriever

        retriever = SelfQueryRetriever(
            llm_provider=mock_llm,
            base_retriever=mock_retriever,
            reranker=mock_reranker,
            embedding_service=mock_embedding,
        )

        query = "查询2024年的财务报告"
        metadata = retriever.extract_metadata(query)

        assert metadata is not None
        assert "year" in metadata
        assert metadata["year"] == 2024

    def test_build_filters_from_metadata(self, mock_llm, mock_retriever, mock_reranker, mock_embedding):
        """Test building filters from extracted metadata."""
        from app.rag.self_query_retriever import SelfQueryRetriever

        retriever = SelfQueryRetriever(
            llm_provider=mock_llm,
            base_retriever=mock_retriever,
            reranker=mock_reranker,
            embedding_service=mock_embedding,
        )

        metadata = {"year": 2024, "document_type": "report"}
        filters = retriever.build_filters(metadata)

        assert filters is not None
        assert "year" in filters
        assert filters["year"]["$eq"] == 2024

    def test_retrieve_with_filters(self, mock_llm, mock_retriever, mock_reranker, mock_embedding):
        """Test retrieval with extracted filters."""
        from app.rag.self_query_retriever import SelfQueryRetriever

        retriever = SelfQueryRetriever(
            llm_provider=mock_llm,
            base_retriever=mock_retriever,
            reranker=mock_reranker,
            embedding_service=mock_embedding,
        )

        chunks, deg_info = retriever.retrieve(kb_id=1, query="查询2024年的财务报告")

        assert chunks is not None
        assert deg_info is not None
        mock_retriever.retrieve.assert_called()

    def test_retrieve_disabled(self, mock_llm, mock_retriever, mock_reranker, mock_embedding):
        """Test retrieval with self-query disabled."""
        from app.rag.self_query_retriever import SelfQueryRetriever

        retriever = SelfQueryRetriever(
            llm_provider=mock_llm,
            base_retriever=mock_retriever,
            reranker=mock_reranker,
            embedding_service=mock_embedding,
            enabled=False,
        )

        chunks, deg_info = retriever.retrieve(kb_id=1, query="test query")

        # When disabled, should fall back to base retriever without LLM call
        assert chunks is not None
        mock_llm.generate.assert_not_called()

    def test_parse_intent_with_date_range(self, mock_llm, mock_retriever, mock_reranker, mock_embedding):
        """Test intent parsing with date range."""
        from app.rag.self_query_retriever import SelfQueryRetriever

        mock_llm.generate.return_value = json.dumps({
            "intent": "filter",
            "metadata": {
                "date_range": {
                    "start": "2023-01-01",
                    "end": "2024-03-31"
                }
            },
            "filter": {
                "created_at": {
                    "$gte": "2023-01-01",
                    "$lte": "2024-03-31"
                }
            },
            "original_query": "2023年3月到2024年3月的销售数据",
        })

        retriever = SelfQueryRetriever(
            llm_provider=mock_llm,
            base_retriever=mock_retriever,
            reranker=mock_reranker,
            embedding_service=mock_embedding,
        )

        query = "2023年3月到2024年3月的销售数据"
        metadata = retriever.extract_metadata(query)

        assert metadata is not None
        assert "date_range" in metadata

    def test_parse_intent_no_filter(self, mock_llm, mock_retriever, mock_reranker, mock_embedding):
        """Test intent parsing when no filter is needed."""
        from app.rag.self_query_retriever import SelfQueryRetriever

        mock_llm.generate.return_value = json.dumps({
            "intent": None,
            "metadata": {},
            "filter": {},
            "original_query": "什么是基金",
        })

        retriever = SelfQueryRetriever(
            llm_provider=mock_llm,
            base_retriever=mock_retriever,
            reranker=mock_reranker,
            embedding_service=mock_embedding,
        )

        query = "什么是基金"
        metadata = retriever.extract_metadata(query)

        assert metadata is not None
        assert metadata == {}

    def test_llm_failure_fallback(self, mock_llm, mock_retriever, mock_reranker, mock_embedding):
        """Test fallback when LLM fails."""
        from app.rag.self_query_retriever import SelfQueryRetriever

        mock_llm.generate.side_effect = Exception("LLM error")

        retriever = SelfQueryRetriever(
            llm_provider=mock_llm,
            base_retriever=mock_retriever,
            reranker=mock_reranker,
            embedding_service=mock_embedding,
        )

        # Should not raise, should fallback to base retriever
        chunks, deg_info = retriever.retrieve(kb_id=1, query="test query")

        assert chunks is not None
        mock_retriever.retrieve.assert_called()


class TestExtractMetadataFromQuery:
    """Tests for metadata extraction helper functions."""

    def test_extract_year_from_query(self):
        """Test extracting year from query text."""
        from app.rag.self_query_retriever import extract_year_from_query

        result = extract_year_from_query("查询2024年的财务报告")
        assert result == 2024

        result = extract_year_from_query("2023年的数据")
        assert result == 2023

        result = extract_year_from_query("没有年份的查询")
        assert result is None

    def test_extract_document_type_from_query(self):
        """Test extracting document type from query text."""
        from app.rag.self_query_retriever import extract_document_type_from_query

        result = extract_document_type_from_query("查询财务报告类型的文档")
        assert result == "财务报告"

        result = extract_document_type_from_query("找一下合同文件")
        assert result is not None

        result = extract_document_type_from_query("普通查询")
        assert result is None

    def test_extract_date_range_from_query(self):
        """Test extracting date range from query text."""
        from app.rag.self_query_retriever import extract_date_range_from_query

        result = extract_date_range_from_query("2023年3月到2024年3月的销售数据")
        assert result is not None
        assert "start" in result
        assert "end" in result

        result = extract_date_range_from_query("没有日期范围的查询")
        assert result is None


class TestSelfQueryRetrieverIntegration:
    """Integration tests for self-query retriever."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        provider = MagicMock()
        provider.generate = MagicMock(return_value=json.dumps({
            "intent": "filter",
            "metadata": {"year": 2024},
            "filter": {"year": {"$eq": 2024}},
            "original_query": "2024年的报告",
        }))
        return provider

    @pytest.fixture
    def mock_retriever(self):
        """Create mock base retriever."""
        retriever = MagicMock()
        retriever.retrieve = MagicMock(return_value=(
            [
                {"chunk_id": 1, "content": "2024年财务报告内容", "distance": 0.1},
                {"chunk_id": 2, "content": "2023年财务报告内容", "distance": 0.2},
            ],
            None,
        ))
        return retriever

    @pytest.fixture
    def mock_reranker(self):
        """Create mock reranker."""
        reranker = MagicMock()
        reranker.rerank = MagicMock(return_value=[
            {"chunk_id": 1, "content": "2024年财务报告内容", "rerank_score": 0.95}
        ])
        return reranker

    @pytest.fixture
    def mock_embedding(self):
        """Create mock embedding service."""
        service = MagicMock()
        service.embed = MagicMock(return_value=[[0.1] * 1024])
        return service

    def test_full_retrieval_flow(self, mock_llm, mock_retriever, mock_reranker, mock_embedding):
        """Test full retrieval flow with self-query."""
        from app.rag.self_query_retriever import SelfQueryRetriever

        retriever = SelfQueryRetriever(
            llm_provider=mock_llm,
            base_retriever=mock_retriever,
            reranker=mock_reranker,
            embedding_service=mock_embedding,
        )

        chunks, deg_info = retriever.retrieve(
            kb_id=1,
            query="2024年的报告",
            top_k=5
        )

        assert chunks is not None
        assert len(chunks) > 0
        assert deg_info is not None
        # LLM should be called for metadata extraction
        mock_llm.generate.assert_called_once()
        # Reranker should be called
        mock_reranker.rerank.assert_called_once()
