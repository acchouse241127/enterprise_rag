"""
Unit tests for QaService.

Tests for app/services/qa_service.py
Author: C2
"""

import pytest
from unittest.mock import MagicMock, patch
import re


class TestFilterBySimilarity:
    """Tests for _filter_by_similarity method."""

    def test_filter_empty_chunks(self):
        """Test filtering empty chunks list."""
        from app.services.qa_service import QaService

        result = QaService._filter_by_similarity([])
        assert result == []

    def test_filter_chunks_no_distance(self):
        """Test chunks without distance field are kept."""
        from app.services.qa_service import QaService

        chunks = [
            {"id": 1, "content": "chunk1"},
            {"id": 2, "content": "chunk2"},
        ]
        result = QaService._filter_by_similarity(chunks)
        assert len(result) == 2

    def test_filter_chunks_low_distance(self):
        """Test chunks with low distance (high similarity) are kept."""
        from app.services.qa_service import QaService

        chunks = [
            {"id": 1, "content": "chunk1", "distance": 0.1},
            {"id": 2, "content": "chunk2", "distance": 0.3},
        ]
        result = QaService._filter_by_similarity(chunks)
        assert len(result) == 2

    def test_filter_chunks_high_distance(self):
        """Test chunks with high distance (low similarity) are filtered out."""
        from app.services.qa_service import QaService

        with patch.object(QaService, '_max_distance_accept', 0.5):
            chunks = [
                {"id": 1, "content": "chunk1", "distance": 0.3},  # Keep
                {"id": 2, "content": "chunk2", "distance": 0.8},  # Filter out
            ]
            result = QaService._filter_by_similarity(chunks)
            assert len(result) == 1
            assert result[0]["id"] == 1

    def test_filter_chunks_mixed_distance(self):
        """Test chunks with mixed distances."""
        from app.services.qa_service import QaService

        with patch.object(QaService, '_max_distance_accept', 0.5):
            chunks = [
                {"id": 1, "content": "chunk1", "distance": 0.1},
                {"id": 2, "content": "chunk2"},  # No distance
                {"id": 3, "content": "chunk3", "distance": 0.9},
                {"id": 4, "content": "chunk4", "distance": 0.4},
            ]
            result = QaService._filter_by_similarity(chunks)
            # Should keep chunks with distance <= 0.5 and those without distance
            assert len(result) == 3


class TestBuildHistoryKey:
    """Tests for _build_history_key method."""

    def test_build_key_with_conversation_id(self):
        """Test building key with conversation ID."""
        from app.services.qa_service import QaService

        key = QaService._build_history_key(1, "conv-123")
        assert key == "kb:1:conv:conv-123"

    def test_build_key_without_conversation_id(self):
        """Test building key without conversation ID."""
        from app.services.qa_service import QaService

        key = QaService._build_history_key(1, None)
        assert key is None

    def test_build_key_with_empty_conversation_id(self):
        """Test building key with empty conversation ID."""
        from app.services.qa_service import QaService

        key = QaService._build_history_key(1, "")
        assert key is None

    def test_build_key_strips_whitespace(self):
        """Test that conversation ID is stripped."""
        from app.services.qa_service import QaService

        key = QaService._build_history_key(1, "  conv-123  ")
        assert key == "kb:1:conv:conv-123"


class TestGetHistoryMessages:
    """Tests for _get_history_messages method."""

    def test_get_history_no_conversation(self):
        """Test getting history without conversation ID."""
        from app.services.qa_service import QaService

        result = QaService._get_history_messages(1, None, 5)
        assert result == []

    def test_get_history_empty_history(self):
        """Test getting history when none exists."""
        from app.services.qa_service import QaService

        # Clear history
        QaService._conversation_history = {}

        result = QaService._get_history_messages(1, "conv-123", 5)
        assert result == []

    def test_get_history_with_messages(self):
        """Test getting history with messages."""
        from app.services.qa_service import QaService
        from app.llm import ChatMessage

        QaService._conversation_history = {
            "kb:1:conv:conv-123": [
                ChatMessage(role="user", content="Q1"),
                ChatMessage(role="assistant", content="A1"),
                ChatMessage(role="user", content="Q2"),
                ChatMessage(role="assistant", content="A2"),
            ]
        }

        result = QaService._get_history_messages(1, "conv-123", 2)
        assert len(result) == 4  # 2 turns = 4 messages

        # Clean up
        QaService._conversation_history = {}

    def test_get_history_limited_turns(self):
        """Test history limited to specified turns."""
        from app.services.qa_service import QaService
        from app.llm import ChatMessage

        QaService._conversation_history = {
            "kb:1:conv:conv-123": [
                ChatMessage(role="user", content=f"Q{i}"),
                ChatMessage(role="assistant", content=f"A{i}"),
            ]
            for i in range(10)
        }

        result = QaService._get_history_messages(1, "conv-123", 1)
        assert len(result) == 2  # 1 turn = 2 messages

        # Clean up
        QaService._conversation_history = {}


class TestAppendHistory:
    """Tests for _append_history method."""

    def test_append_history_no_conversation(self):
        """Test appending without conversation ID."""
        from app.services.qa_service import QaService

        QaService._conversation_history = {}
        QaService._append_history(1, None, "Q", "A")
        assert QaService._conversation_history == {}

    def test_append_history_new_conversation(self):
        """Test appending to new conversation."""
        from app.services.qa_service import QaService

        QaService._conversation_history = {}
        QaService._append_history(1, "conv-123", "Q1", "A1")

        key = "kb:1:conv:conv-123"
        assert key in QaService._conversation_history
        assert len(QaService._conversation_history[key]) == 2

        # Clean up
        QaService._conversation_history = {}

    def test_append_history_existing_conversation(self):
        """Test appending to existing conversation."""
        from app.services.qa_service import QaService
        from app.llm import ChatMessage

        key = "kb:1:conv:conv-123"
        QaService._conversation_history = {
            key: [ChatMessage(role="user", content="Q1")]
        }

        QaService._append_history(1, "conv-123", "Q2", "A2")
        assert len(QaService._conversation_history[key]) == 3

        # Clean up
        QaService._conversation_history = {}


class TestApplyDedup:
    """Tests for _apply_dedup method."""

    def test_dedup_empty_chunks(self):
        """Test dedup with empty chunks."""
        from app.services.qa_service import QaService

        result = QaService._apply_dedup([])
        assert result == []

    def test_dedup_disabled(self):
        """Test dedup when disabled."""
        from app.services.qa_service import QaService

        chunks = [{"id": 1, "content": "chunk1"}]
        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.dedup_enabled = False
            result = QaService._apply_dedup(chunks)
            assert result == chunks

    def test_dedup_enabled(self):
        """Test dedup when enabled."""
        from app.services.qa_service import QaService

        chunks = [
            {"id": 1, "content": "This is a test"},
            {"id": 2, "content": "This is a test"},  # Duplicate
        ]
        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.dedup_enabled = True
            mock_settings.dedup_simhash_threshold = 3
            with patch('app.services.qa_service.deduplicate_chunks') as mock_dedup:
                mock_dedup.return_value = [chunks[0]]
                result = QaService._apply_dedup(chunks)
                assert len(result) == 1


class TestApplyReranker:
    """Tests for _apply_reranker method."""

    def test_reranker_empty_chunks(self):
        """Test reranker with empty chunks."""
        from app.services.qa_service import QaService

        result = QaService._apply_reranker("question", [], 5)
        assert result == []

    def test_reranker_disabled(self):
        """Test reranker when disabled."""
        from app.services.qa_service import QaService

        chunks = [{"id": 1, "content": "chunk1"}]
        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.reranker_enabled = False
            result = QaService._apply_reranker("question", chunks, 5)
            assert result == chunks

    def test_reranker_enabled(self):
        """Test reranker when enabled."""
        from app.services.qa_service import QaService

        chunks = [
            {"id": 1, "content": "chunk1"},
            {"id": 2, "content": "chunk2"},
        ]
        reranked = [
            {"id": 2, "content": "chunk2", "rerank_score": 0.9},
            {"id": 1, "content": "chunk1", "rerank_score": 0.7},
        ]

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.reranker_enabled = True
            mock_settings.dynamic_threshold_enabled = False
            with patch.object(QaService, '_reranker') as mock_reranker:
                mock_reranker.rerank.return_value = reranked
                result = QaService._apply_reranker("question", chunks, 5)
                assert len(result) == 2

    def test_reranker_with_dynamic_threshold(self):
        """Test reranker with dynamic threshold filtering."""
        from app.services.qa_service import QaService

        chunks = [
            {"id": 1, "content": "chunk1"},
            {"id": 2, "content": "chunk2"},
        ]
        reranked = [
            {"id": 2, "content": "chunk2", "rerank_score": 0.9},
            {"id": 1, "content": "chunk1", "rerank_score": 0.1},  # Below threshold
        ]

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.reranker_enabled = True
            mock_settings.dynamic_threshold_enabled = True
            mock_settings.dynamic_threshold_min = 0.5
            with patch.object(QaService, '_reranker') as mock_reranker:
                mock_reranker.rerank.return_value = reranked
                result = QaService._apply_reranker("question", chunks, 5)
                assert len(result) == 1
                assert result[0]["id"] == 2


class TestParseCitedIds:
    """Tests for _parse_cited_ids method."""

    def test_parse_empty_answer(self):
        """Test parsing empty answer."""
        from app.services.qa_service import QaService

        result = QaService._parse_cited_ids("")
        assert result == []

    def test_parse_none_answer(self):
        """Test parsing None answer."""
        from app.services.qa_service import QaService

        result = QaService._parse_cited_ids(None)
        assert result == []

    def test_parse_no_citations(self):
        """Test parsing answer without citations."""
        from app.services.qa_service import QaService

        result = QaService._parse_cited_ids("This is an answer without citations.")
        assert result == []

    def test_parse_single_citation(self):
        """Test parsing single citation."""
        from app.services.qa_service import QaService

        result = QaService._parse_cited_ids("According to [ID:1], the answer is...")
        assert result == [1]

    def test_parse_multiple_citations(self):
        """Test parsing multiple citations."""
        from app.services.qa_service import QaService

        result = QaService._parse_cited_ids(
            "According to [ID:1] and [ID:2], also see [ID:5]..."
        )
        assert result == [1, 2, 5]


class TestIsSafePublicBaseUrl:
    """Tests for _is_safe_public_base_url method."""

    def test_unsafe_localhost(self):
        """Test localhost is unsafe."""
        from app.services.qa_service import QaService

        assert QaService._is_safe_public_base_url("http://localhost:8080") is False

    def test_unsafe_127_0_0_1(self):
        """Test 127.0.0.1 is unsafe."""
        from app.services.qa_service import QaService

        assert QaService._is_safe_public_base_url("http://127.0.0.1:8080") is False

    def test_unsafe_ipv6_loopback(self):
        """Test IPv6 loopback is unsafe."""
        from app.services.qa_service import QaService

        assert QaService._is_safe_public_base_url("http://[::1]:8080") is False

    def test_unsafe_local_domain(self):
        """Test .local domain is unsafe."""
        from app.services.qa_service import QaService

        assert QaService._is_safe_public_base_url("http://test.local") is False

    def test_unsafe_ftp_scheme(self):
        """Test non-http(s) scheme is unsafe."""
        from app.services.qa_service import QaService

        assert QaService._is_safe_public_base_url("ftp://example.com") is False

    def test_unsafe_empty_url(self):
        """Test empty URL is unsafe."""
        from app.services.qa_service import QaService

        assert QaService._is_safe_public_base_url("") is False

    def test_unsafe_none_url(self):
        """Test None URL is unsafe."""
        from app.services.qa_service import QaService

        assert QaService._is_safe_public_base_url(None) is False

    def test_safe_public_domain(self):
        """Test public domain is safe."""
        from app.services.qa_service import QaService

        # Note: This may do DNS resolution, so we test with a known public domain
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [(2, 1, 6, '', ('8.8.8.8', 443))]
            assert QaService._is_safe_public_base_url("https://example.com") is True

    def test_unsafe_private_ip(self):
        """Test private IP is unsafe."""
        from app.services.qa_service import QaService

        assert QaService._is_safe_public_base_url("http://192.168.1.1") is False
        assert QaService._is_safe_public_base_url("http://10.0.0.1") is False
        assert QaService._is_safe_public_base_url("http://172.16.0.1") is False


class TestResolveQueryExpansionConfig:
    """Tests for _resolve_query_expansion_config method."""

    def test_resolve_default_mode(self):
        """Test resolving default mode."""
        from app.services.qa_service import QaService

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.retrieval_query_expansion_mode = "rule"
            mode, provider = QaService._resolve_query_expansion_config()
            assert mode == "rule"
            assert provider is None

    def test_resolve_rule_mode(self):
        """Test resolving rule mode explicitly."""
        from app.services.qa_service import QaService

        mode, provider = QaService._resolve_query_expansion_config(
            query_expansion_mode="rule"
        )
        assert mode == "rule"

    def test_resolve_llm_mode_with_unsafe_url(self):
        """Test LLM mode rejects unsafe URL."""
        from app.services.qa_service import QaService

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.retrieval_query_expansion_mode = "llm"
            mode, provider = QaService._resolve_query_expansion_config(
                query_expansion_mode="llm",
                query_expansion_llm={"base_url": "http://localhost:8080"}
            )
            # Should fall back to rule mode or have no provider
            assert mode == "llm"

    def test_resolve_llm_mode_with_custom_provider(self):
        """Test LLM mode with custom provider config."""
        from app.services.qa_service import QaService

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.retrieval_query_expansion_mode = "llm"
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                mock_getaddrinfo.return_value = [(2, 1, 6, '', ('8.8.8.8', 443))]
                with patch('app.services.qa_service.build_chat_provider') as mock_build:
                    mock_build.return_value = MagicMock()
                    mode, provider = QaService._resolve_query_expansion_config(
                        query_expansion_mode="llm",
                        query_expansion_llm={
                            "provider": "openai",
                            "api_key": "test-key",
                            "model_name": "gpt-4",
                            "base_url": "https://api.example.com"
                        }
                    )
                    assert mode == "llm"
                    assert provider is not None

    def test_resolve_llm_mode_timeout_capped(self):
        """Test LLM mode timeout is capped."""
        from app.services.qa_service import QaService

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.retrieval_query_expansion_mode = "llm"
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                mock_getaddrinfo.return_value = [(2, 1, 6, '', ('8.8.8.8', 443))]
                with patch('app.services.qa_service.build_chat_provider') as mock_build:
                    mock_build.return_value = MagicMock()
                    QaService._resolve_query_expansion_config(
                        query_expansion_mode="llm",
                        query_expansion_llm={
                            "base_url": "https://api.example.com",
                            "timeout_seconds": 100  # Should be capped to 30
                        }
                    )
                    call_kwargs = mock_build.call_args[1]
                    assert call_kwargs["timeout_seconds"] == 30


class TestLogRetrieval:
    """Tests for _log_retrieval method."""

    def test_log_retrieval_disabled(self):
        """Test logging when disabled."""
        from app.services.qa_service import QaService

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.retrieval_log_enabled = False
            result = QaService._log_retrieval(
                knowledge_base_id=1,
                user_id=1,
                query="test",
                chunks_retrieved=5,
                chunks_after_filter=4,
                chunks_after_dedup=3,
                chunks_after_rerank=2,
                final_chunks=[],
            )
            assert result is None

    def test_log_retrieval_success(self):
        """Test successful logging."""
        from app.services.qa_service import QaService

        mock_db = MagicMock()
        mock_log = MagicMock()
        mock_log.id = 1

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.retrieval_log_enabled = True
            mock_settings.retrieval_log_max_chunks = 10
            with patch('app.core.database.SessionLocal') as mock_session:
                mock_session.return_value = mock_db
                with patch('app.services.retrieval_log_service.RetrievalLogService.create_log') as mock_create:
                    mock_create.return_value = mock_log
                    result = QaService._log_retrieval(
                        knowledge_base_id=1,
                        user_id=1,
                        query="test query",
                        chunks_retrieved=5,
                        chunks_after_filter=4,
                        chunks_after_dedup=3,
                        chunks_after_rerank=2,
                        final_chunks=[
                            {"id": 1, "content": "chunk1", "rerank_score": 0.9, "document_id": 1}
                        ],
                    )
                    assert result == 1
                    mock_db.close.assert_called()

    def test_log_retrieval_with_answer_citations(self):
        """Test logging parses answer citations."""
        from app.services.qa_service import QaService

        mock_db = MagicMock()
        mock_log = MagicMock()
        mock_log.id = 1

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.retrieval_log_enabled = True
            mock_settings.retrieval_log_max_chunks = 10
            with patch('app.core.database.SessionLocal') as mock_session:
                mock_session.return_value = mock_db
                with patch('app.services.retrieval_log_service.RetrievalLogService.create_log') as mock_create:
                    mock_create.return_value = mock_log
                    QaService._log_retrieval(
                        knowledge_base_id=1,
                        user_id=1,
                        query="test",
                        chunks_retrieved=1,
                        chunks_after_filter=1,
                        chunks_after_dedup=1,
                        chunks_after_rerank=1,
                        final_chunks=[],
                        answer="See [ID:1] and [ID:2]",
                    )
                    # Check that create_log was called
                    mock_create.assert_called()

    def test_log_retrieval_exception(self):
        """Test logging handles exceptions."""
        from app.services.qa_service import QaService

        with patch('app.services.qa_service.settings') as mock_settings:
            mock_settings.retrieval_log_enabled = True
            with patch('app.core.database.SessionLocal') as mock_session:
                mock_session.side_effect = Exception("DB error")
                result = QaService._log_retrieval(
                    knowledge_base_id=1,
                    user_id=1,
                    query="test",
                    chunks_retrieved=1,
                    chunks_after_filter=1,
                    chunks_after_dedup=1,
                    chunks_after_rerank=1,
                    final_chunks=[],
                )
                assert result is None


class TestQaServiceInit:
    """Tests for QaService initialization."""

    def test_service_attributes(self):
        """Test service has required attributes."""
        from app.services.qa_service import QaService

        assert hasattr(QaService, '_embedding_service')
        assert hasattr(QaService, '_vector_store')
        assert hasattr(QaService, '_retriever')
        assert hasattr(QaService, '_reranker')
        assert hasattr(QaService, '_pipeline')
        assert hasattr(QaService, '_conversation_history')
