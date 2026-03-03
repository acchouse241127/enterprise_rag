"""
Query cache service tests.

Tests for the two-layer caching system:
1. Exact match cache (Redis)
2. Semantic match cache (Vector similarity)

Author: C2
Date: 2026-03-03
"""

import json
from unittest.mock import Mock, MagicMock, patch
import pytest

# Mock numpy to avoid import conflicts
import sys
from unittest.mock import MagicMock as MockMagic
sys.modules['numpy'] = MockMagic()
sys.modules['numpy.linalg'] = MockMagic()


class TestGetRedisClient:
    """Tests for get_redis_client function."""

    @patch("app.cache.query_cache.redis.from_url")
    @patch("app.cache.query_cache.settings.redis_url", "redis://localhost:6379/0")
    def test_get_redis_client_success(self, mock_from_url):
        """Test successful Redis client creation."""
        from app.cache.query_cache import get_redis_client

        mock_redis = Mock()
        mock_from_url.return_value = mock_redis

        result = get_redis_client()
        assert result == mock_redis
        mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)

    @patch("app.cache.query_cache.redis.from_url")
    @patch("app.cache.query_cache.settings.redis_url", "redis://localhost:6379/0")
    def test_get_redis_client_failure(self, mock_from_url):
        """Test Redis client creation failure."""
        from app.cache.query_cache import get_redis_client

        mock_from_url.side_effect = Exception("Connection failed")

        result = get_redis_client()
        assert result is None


class TestExactCacheStore:
    """Tests for ExactCacheStore class."""

    def test_init(self):
        """Test ExactCacheStore initialization."""
        from app.cache.query_cache import ExactCacheStore

        store = ExactCacheStore(redis_client=None)
        assert store._redis is None

        mock_redis = Mock()
        store = ExactCacheStore(redis_client=mock_redis)
        assert store._redis == mock_redis

    def test_redis_property_lazy_load(self):
        """Test Redis property lazy loading."""
        from app.cache.query_cache import ExactCacheStore

        store = ExactCacheStore(redis_client=None)

        with patch("app.cache.query_cache.get_redis_client") as mock_get_client:
            mock_redis = Mock()
            mock_get_client.return_value = mock_redis

            redis = store.redis
            assert redis == mock_redis
            mock_get_client.assert_called_once()

            # Second call should use cached value
            redis2 = store.redis
            assert redis2 == mock_redis
            assert mock_get_client.call_count == 1

    def test_build_cache_key(self):
        """Test cache key building."""
        from app.cache.query_cache import ExactCacheStore

        store = ExactCacheStore()

        key = store.build_cache_key(1, "test query")
        assert "qa:cache:kb:1:query:" in key
        assert len(key) > 20

        # Same query should produce same key
        key2 = store.build_cache_key(1, "test query")
        assert key == key2

        # Different kb_id should produce different key
        key3 = store.build_cache_key(2, "test query")
        assert key != key3

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    def test_get_cache_hit(self):
        """Test cache get with hit."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        store = ExactCacheStore(redis_client=mock_redis)

        cached_data = {"answer": "test answer", "sources": []}
        mock_redis.get.return_value = json.dumps(cached_data, ensure_ascii=False)

        result = store.get(1, "test query")
        assert result == cached_data
        mock_redis.get.assert_called_once()

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    def test_get_cache_miss(self):
        """Test cache get with miss."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        store = ExactCacheStore(redis_client=mock_redis)
        mock_redis.get.return_value = None

        result = store.get(1, "test query")
        assert result is None

    @patch("app.cache.query_cache.settings.cache_enabled", False)
    def test_get_cache_disabled(self):
        """Test cache get when disabled."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        store = ExactCacheStore(redis_client=mock_redis)

        result = store.get(1, "test query")
        assert result is None
        mock_redis.get.assert_not_called()

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    @patch("app.cache.query_cache.settings.cache_default_ttl_seconds", 3600)
    def test_set_cache_success(self):
        """Test cache set success."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        store = ExactCacheStore(redis_client=mock_redis)

        data = {"answer": "test answer"}
        result = store.set(1, "test query", data)
        assert result is True
        mock_redis.setex.assert_called_once()

    @patch("app.cache.query_cache.settings.cache_enabled", False)
    def test_set_cache_disabled(self):
        """Test cache set when disabled."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        store = ExactCacheStore(redis_client=mock_redis)

        data = {"answer": "test answer"}
        result = store.set(1, "test query", data)
        assert result is False
        mock_redis.setex.assert_not_called()

    def test_set_cache_failure(self):
        """Test cache set failure."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        mock_redis.setex.side_effect = Exception("Redis error")
        store = ExactCacheStore(redis_client=mock_redis)

        data = {"answer": "test answer"}
        result = store.set(1, "test query", data)
        assert result is False

    def test_delete_by_kb_success(self):
        """Test delete by knowledge base success."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        mock_redis.keys.return_value = ["key1", "key2"]
        mock_redis.delete.return_value = 2
        store = ExactCacheStore(redis_client=mock_redis)

        result = store.delete_by_kb(1)
        assert result == 2
        mock_redis.keys.assert_called_once_with("qa:cache:kb:1:query:*")
        mock_redis.delete.assert_called_once_with("key1", "key2")

    def test_delete_by_kb_no_keys(self):
        """Test delete by knowledge base with no keys."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        mock_redis.keys.return_value = []
        store = ExactCacheStore(redis_client=mock_redis)

        result = store.delete_by_kb(1)
        assert result == 0
        mock_redis.delete.assert_not_called()

    def test_delete_by_kb_failure(self):
        """Test delete by knowledge base failure."""
        from app.cache.query_cache import ExactCacheStore

        mock_redis = Mock()
        mock_redis.keys.side_effect = Exception("Redis error")
        store = ExactCacheStore(redis_client=mock_redis)

        result = store.delete_by_kb(1)
        assert result == 0


class TestSemanticCacheMatcher:
    """Tests for SemanticCacheMatcher class."""

    def test_init(self):
        """Test SemanticCacheMatcher initialization."""
        from app.cache.query_cache import SemanticCacheMatcher

        matcher = SemanticCacheMatcher(redis_client=None, embedding_service=None)
        assert matcher._redis is None
        assert matcher._embedding_service is None

        mock_redis = Mock()
        mock_embedding = Mock()
        matcher = SemanticCacheMatcher(redis_client=mock_redis, embedding_service=mock_embedding)
        assert matcher._redis == mock_redis
        assert matcher._embedding_service == mock_embedding

    def test_redis_property_lazy_load(self):
        """Test Redis property lazy loading."""
        from app.cache.query_cache import SemanticCacheMatcher

        matcher = SemanticCacheMatcher(redis_client=None)

        with patch("app.cache.query_cache.get_redis_client") as mock_get_client:
            mock_redis = Mock()
            mock_get_client.return_value = mock_redis

            redis = matcher.redis
            assert redis == mock_redis
            mock_get_client.assert_called_once()

    def test_get_index_key(self):
        """Test index key generation."""
        from app.cache.query_cache import SemanticCacheMatcher

        matcher = SemanticCacheMatcher()

        key = matcher._get_index_key(1)
        assert key == "qa:semantic:kb:1:index"

    @patch("app.cache.query_cache.BgeM3EmbeddingService")
    @patch("app.cache.query_cache.settings.embedding_model_name", "model")
    @patch("app.cache.query_cache.settings.embedding_fallback_dim", 768)
    def test_get_embedding_lazy_init(self, mock_embedding_class):
        """Test embedding service lazy initialization."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_embedding_service = Mock()
        mock_embedding_service.embed.return_value = [0.1, 0.2, 0.3]
        mock_embedding_class.return_value = mock_embedding_service

        matcher = SemanticCacheMatcher()

        embedding = matcher._get_embedding("test query")
        assert embedding == [0.1, 0.2, 0.3]
        mock_embedding_class.assert_called_once()

        # Second call should use cached service
        embedding2 = matcher._get_embedding("test query")
        assert embedding2 == [0.1, 0.2, 0.3]
        assert mock_embedding_class.call_count == 1

    @patch("app.cache.query_cache.np")
    def test_cosine_similarity(self, mock_np):
        """Test cosine similarity calculation."""
        from app.cache.query_cache import SemanticCacheMatcher

        # Mock numpy operations
        mock_np.array.side_effect = lambda x: x
        mock_np.dot.return_value = 1.0
        mock_np.linalg.norm.return_value = 1.0

        matcher = SemanticCacheMatcher()

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = matcher._cosine_similarity(vec1, vec2)
        assert similarity == 1.0

        # Test different vectors
        mock_np.dot.return_value = 0.0
        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]
        similarity = matcher._cosine_similarity(vec3, vec4)
        assert similarity == 0.0

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    @patch("app.cache.query_cache.settings.cache_semantic_threshold", 0.85)
    def test_find_semantic_match_hit(self):
        """Test semantic cache hit."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        mock_embedding = Mock()
        mock_embedding.embed.return_value = [0.9, 0.1, 0.0]

        matcher = SemanticCacheMatcher(redis_client=mock_redis, embedding_service=mock_embedding)

        index_data = {
            "queries": [
                {
                    "query": "similar query",
                    "embedding": [0.95, 0.05, 0.0],
                    "data": {"answer": "cached answer"}
                }
            ]
        }
        mock_redis.get.return_value = json.dumps(index_data, ensure_ascii=False)

        result = matcher.find_semantic_match(1, "test query")
        assert result is not None
        assert result["cache_type"] == "semantic"
        assert "similarity_score" in result
        assert result["answer"] == "cached answer"

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    @patch("app.cache.query_cache.settings.cache_semantic_threshold", 0.95)
    def test_find_semantic_match_below_threshold(self):
        """Test semantic cache below threshold."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        mock_embedding = Mock()
        mock_embedding.embed.return_value = [0.5, 0.5, 0.0]

        matcher = SemanticCacheMatcher(redis_client=mock_redis, embedding_service=mock_embedding)

        index_data = {
            "queries": [
                {
                    "query": "different query",
                    "embedding": [0.0, 0.5, 0.5],
                    "data": {"answer": "cached answer"}
                }
            ]
        }
        mock_redis.get.return_value = json.dumps(index_data, ensure_ascii=False)

        result = matcher.find_semantic_match(1, "test query")
        assert result is None

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    def test_find_semantic_match_no_index(self):
        """Test semantic cache with no index."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_embedding = Mock()

        matcher = SemanticCacheMatcher(redis_client=mock_redis, embedding_service=mock_embedding)

        result = matcher.find_semantic_match(1, "test query")
        assert result is None

    @patch("app.cache.query_cache.settings.cache_enabled", False)
    def test_find_semantic_match_disabled(self):
        """Test semantic cache when disabled."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        mock_embedding = Mock()

        matcher = SemanticCacheMatcher(redis_client=mock_redis, embedding_service=mock_embedding)

        result = matcher.find_semantic_match(1, "test query")
        assert result is None
        mock_redis.get.assert_not_called()

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    @patch("app.cache.query_cache.settings.cache_max_entries_per_kb", 100)
    @patch("app.cache.query_cache.settings.cache_default_ttl_seconds", 3600)
    def test_add_to_index_new(self):
        """Test adding to semantic index (new)."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_embedding = Mock()
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]

        matcher = SemanticCacheMatcher(redis_client=mock_redis, embedding_service=mock_embedding)

        data = {"answer": "test answer"}
        result = matcher.add_to_index(1, "test query", data)
        assert result is True
        mock_redis.setex.assert_called_once()

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    @patch("app.cache.query_cache.settings.cache_max_entries_per_kb", 2)
    @patch("app.cache.query_cache.settings.cache_default_ttl_seconds", 3600)
    def test_add_to_index_max_entries(self):
        """Test adding to semantic index with max entries limit."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_embedding = Mock()
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]

        matcher = SemanticCacheMatcher(redis_client=mock_redis, embedding_service=mock_embedding)

        data = {"answer": "test answer"}
        matcher.add_to_index(1, "query1", data)
        matcher.add_to_index(1, "query2", data)
        matcher.add_to_index(1, "query3", data)

        # Verify setex was called 3 times
        assert mock_redis.setex.call_count == 3

    @patch("app.cache.query_cache.settings.cache_enabled", False)
    def test_add_to_index_disabled(self):
        """Test adding to semantic index when disabled."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        mock_embedding = Mock()

        matcher = SemanticCacheMatcher(redis_client=mock_redis, embedding_service=mock_embedding)

        data = {"answer": "test answer"}
        result = matcher.add_to_index(1, "test query", data)
        assert result is False
        mock_redis.setex.assert_not_called()

    def test_delete_by_kb_success(self):
        """Test delete by knowledge base success."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        matcher = SemanticCacheMatcher(redis_client=mock_redis)

        result = matcher.delete_by_kb(1)
        assert result is True
        mock_redis.delete.assert_called_once_with("qa:semantic:kb:1:index")

    def test_delete_by_kb_failure(self):
        """Test delete by knowledge base failure."""
        from app.cache.query_cache import SemanticCacheMatcher

        mock_redis = Mock()
        mock_redis.delete.side_effect = Exception("Redis error")
        matcher = SemanticCacheMatcher(redis_client=mock_redis)

        result = matcher.delete_by_kb(1)
        assert result is False


class TestQueryCacheService:
    """Tests for QueryCacheService class."""

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    def test_init_default(self):
        """Test QueryCacheService default initialization."""
        from app.cache.query_cache import QueryCacheService

        service = QueryCacheService()
        assert service._enabled is True
        assert service._exact_store is not None
        assert service._semantic_matcher is not None

    @patch("app.cache.query_cache.settings.cache_enabled", False)
    def test_init_disabled(self):
        """Test QueryCacheService disabled initialization."""
        from app.cache.query_cache import QueryCacheService

        service = QueryCacheService(enabled=False)
        assert service._enabled is False

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    def test_get_exact_match(self):
        """Test get with exact match."""
        from app.cache.query_cache import QueryCacheService, ExactCacheStore

        mock_exact = Mock(spec=ExactCacheStore)
        mock_exact.get.return_value = {"answer": "test answer"}
        mock_semantic = Mock()

        service = QueryCacheService(enabled=True, exact_store=mock_exact, semantic_matcher=mock_semantic)

        result = service.get(1, "test query")
        assert result is not None
        assert result["cache_type"] == "exact"
        mock_exact.get.assert_called_once_with(1, "test query")
        mock_semantic.find_semantic_match.assert_not_called()

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    def test_get_semantic_match(self):
        """Test get with semantic match."""
        from app.cache.query_cache import QueryCacheService, ExactCacheStore

        mock_exact = Mock(spec=ExactCacheStore)
        mock_exact.get.return_value = None
        mock_semantic = Mock()
        mock_semantic.find_semantic_match.return_value = {"answer": "test answer"}

        service = QueryCacheService(enabled=True, exact_store=mock_exact, semantic_matcher=mock_semantic)

        result = service.get(1, "test query")
        assert result is not None
        mock_exact.get.assert_called_once_with(1, "test query")
        mock_semantic.find_semantic_match.assert_called_once()

    @patch("app.cache.query_cache.settings.cache_enabled", False)
    def test_get_disabled(self):
        """Test get when cache disabled."""
        from app.cache.query_cache import QueryCacheService, ExactCacheStore

        mock_exact = Mock(spec=ExactCacheStore)
        mock_semantic = Mock()

        service = QueryCacheService(enabled=False, exact_store=mock_exact, semantic_matcher=mock_semantic)

        result = service.get(1, "test query")
        assert result is None
        mock_exact.get.assert_not_called()
        mock_semantic.find_semantic_match.assert_not_called()

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    def test_get_cache_miss(self):
        """Test get with cache miss."""
        from app.cache.query_cache import QueryCacheService, ExactCacheStore

        mock_exact = Mock(spec=ExactCacheStore)
        mock_exact.get.return_value = None
        mock_semantic = Mock()
        mock_semantic.find_semantic_match.return_value = None

        service = QueryCacheService(enabled=True, exact_store=mock_exact, semantic_matcher=mock_semantic)

        result = service.get(1, "test query")
        assert result is None

    @patch("app.cache.query_cache.settings.cache_enabled", True)
    def test_set_success(self):
        """Test set success."""
        from app.cache.query_cache import QueryCacheService, ExactCacheStore

        mock_exact = Mock(spec=ExactCacheStore)
        mock_exact.set.return_value = True
        mock_semantic = Mock()
        mock_semantic.add_to_index.return_value = True

        service = QueryCacheService(enabled=True, exact_store=mock_exact, semantic_matcher=mock_semantic)

        data = {"answer": "test answer"}
        result = service.set(1, "test query", data)
        assert result is True
        mock_exact.set.assert_called_once()
        mock_semantic.add_to_index.assert_called_once()

    @patch("app.cache.query_cache.settings.cache_enabled", False)
    def test_set_disabled(self):
        """Test set when disabled."""
        from app.cache.query_cache import QueryCacheService, ExactCacheStore

        mock_exact = Mock(spec=ExactCacheStore)
        mock_semantic = Mock()

        service = QueryCacheService(enabled=False, exact_store=mock_exact, semantic_matcher=mock_semantic)

        data = {"answer": "test answer"}
        result = service.set(1, "test query", data)
        assert result is False
        mock_exact.set.assert_not_called()
        mock_semantic.add_to_index.assert_not_called()

    def test_invalidate_kb(self):
        """Test invalidate knowledge base."""
        from app.cache.query_cache import QueryCacheService, ExactCacheStore

        mock_exact = Mock(spec=ExactCacheStore)
        mock_exact.delete_by_kb.return_value = 5
        mock_semantic = Mock()
        mock_semantic.delete_by_kb.return_value = True

        service = QueryCacheService(enabled=True, exact_store=mock_exact, semantic_matcher=mock_semantic)

        service.invalidate_kb(1)
        mock_exact.delete_by_kb.assert_called_once_with(1)
        mock_semantic.delete_by_kb.assert_called_once_with(1)


class TestCacheInvalidator:
    """Tests for CacheInvalidator class."""

    def test_init_default(self):
        """Test CacheInvalidator default initialization."""
        from app.cache.query_cache import CacheInvalidator

        invalidator = CacheInvalidator()
        assert invalidator._cache_service is not None

    def test_on_document_change_add(self):
        """Test on document change (add)."""
        from app.cache.query_cache import CacheInvalidator, QueryCacheService

        mock_cache = Mock(spec=QueryCacheService)
        invalidator = CacheInvalidator(cache_service=mock_cache)

        invalidator.on_document_change(1, "add")
        mock_cache.invalidate_kb.assert_called_once_with(1)

    def test_on_document_change_update(self):
        """Test on document change (update)."""
        from app.cache.query_cache import CacheInvalidator, QueryCacheService

        mock_cache = Mock(spec=QueryCacheService)
        invalidator = CacheInvalidator(cache_service=mock_cache)

        invalidator.on_document_change(1, "update")
        mock_cache.invalidate_kb.assert_called_once_with(1)

    def test_on_document_change_delete(self):
        """Test on document change (delete)."""
        from app.cache.query_cache import CacheInvalidator, QueryCacheService

        mock_cache = Mock(spec=QueryCacheService)
        invalidator = CacheInvalidator(cache_service=mock_cache)

        invalidator.on_document_change(1, "delete")
        mock_cache.invalidate_kb.assert_called_once_with(1)

    def test_on_document_change_other(self):
        """Test on document change (other action)."""
        from app.cache.query_cache import CacheInvalidator, QueryCacheService

        mock_cache = Mock(spec=QueryCacheService)
        invalidator = CacheInvalidator(cache_service=mock_cache)

        invalidator.on_document_change(1, "read")
        mock_cache.invalidate_kb.assert_not_called()

    def test_on_chunk_change(self):
        """Test on chunk change."""
        from app.cache.query_cache import CacheInvalidator, QueryCacheService

        mock_cache = Mock(spec=QueryCacheService)
        invalidator = CacheInvalidator(cache_service=mock_cache)

        invalidator.on_chunk_change(1)
        mock_cache.invalidate_kb.assert_called_once_with(1)

    def test_on_knowledge_base_delete(self):
        """Test on knowledge base delete."""
        from app.cache.query_cache import CacheInvalidator, QueryCacheService

        mock_cache = Mock(spec=QueryCacheService)
        invalidator = CacheInvalidator(cache_service=mock_cache)

        invalidator.on_knowledge_base_delete(1)
        mock_cache.invalidate_kb.assert_called_once_with(1)
