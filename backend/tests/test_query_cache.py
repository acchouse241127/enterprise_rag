"""Comprehensive tests for QueryCache module.

Tests cover:
- ExactCacheStore functionality
- SemanticCacheMatcher functionality
- QueryCacheService orchestration
- CacheInvalidator helper
"""

import json
import pytest
from unittest.mock import MagicMock, patch, call


class TestExactCacheStore:
    """Tests for ExactCacheStore."""

    def test_exact_cache_store_init(self):
        """Test ExactCacheStore initialization."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        store = ExactCacheStore(redis_client=mock_redis)
        assert store._redis is mock_redis

    def test_exact_cache_store_redis_property_none(self):
        """Test redis property when _redis is None."""
        from app.cache.query_cache import ExactCacheStore, get_redis_client
        
        with patch('app.cache.query_cache.get_redis_client') as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            
            store = ExactCacheStore()
            assert store._redis is None
            assert store.redis is mock_redis
            assert store._redis is mock_redis

    def test_build_cache_key(self):
        """Test build_cache_key method."""
        from app.cache.query_cache import ExactCacheStore
        
        store = ExactCacheStore()
        key = store.build_cache_key(kb_id=123, query="test query")
        assert key.startswith("qa:cache:kb:123:query:")
        assert len(key) == len("qa:cache:kb:123:query:") + 32  # 32 char hash

    def test_build_cache_key_consistency(self):
        """Test that same query produces same key."""
        from app.cache.query_cache import ExactCacheStore
        
        store = ExactCacheStore()
        key1 = store.build_cache_key(kb_id=1, query="test")
        key2 = store.build_cache_key(kb_id=1, query="test")
        assert key1 == key2

    def test_build_cache_key_different_kb(self):
        """Test that different KBs produce different keys."""
        from app.cache.query_cache import ExactCacheStore
        
        store = ExactCacheStore()
        key1 = store.build_cache_key(kb_id=1, query="test")
        key2 = store.build_cache_key(kb_id=2, query="test")
        assert key1 != key2

    def test_get_cache_hit(self):
        """Test get when cache hits."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({"answer": "test answer"})
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.get(kb_id=1, query="test")
            
            assert result == {"answer": "test answer"}
            mock_redis.get.assert_called_once()

    def test_get_cache_miss(self):
        """Test get when cache misses."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.get(kb_id=1, query="test")
            
            assert result is None

    def test_get_cache_disabled(self):
        """Test get when cache is disabled."""
        from app.cache.query_cache import ExactCacheStore
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = False
            mock_redis = MagicMock()
            
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.get(kb_id=1, query="test")
            
            assert result is None
            mock_redis.get.assert_not_called()

    def test_get_json_decode_error(self):
        """Test get when JSON decode fails."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = "invalid json"
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.get(kb_id=1, query="test")
            
            assert result is None

    def test_get_exception(self):
        """Test get when exception occurs."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis error")
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.get(kb_id=1, query="test")
            
            assert result is None

    def test_set_success(self):
        """Test set when successful."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            mock_settings.cache_default_ttl_seconds = 3600
            
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.set(kb_id=1, query="test", data={"answer": "test"})
            
            assert result is True
            mock_redis.setex.assert_called_once()

    def test_set_with_custom_ttl(self):
        """Test set with custom TTL."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            mock_settings.cache_default_ttl_seconds = 3600
            
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.set(kb_id=1, query="test", data={}, ttl_seconds=7200)
            
            assert result is True
            # Verify TTL was passed
            call_args = mock_redis.setex.call_args
            # setex(key, ttl, value) - TTL is second argument (index 1)
            if call_args[0]:
                assert 7200 in call_args[0]

    def test_set_cache_disabled(self):
        """Test set when cache is disabled."""
        from app.cache.query_cache import ExactCacheStore
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = False
            mock_redis = MagicMock()
            
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.set(kb_id=1, query="test", data={})
            
            assert result is False
            mock_redis.setex.assert_not_called()

    def test_set_exception(self):
        """Test set when exception occurs."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("Redis error")
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            mock_settings.cache_default_ttl_seconds = 3600
            
            store = ExactCacheStore(redis_client=mock_redis)
            result = store.set(kb_id=1, query="test", data={})
            
            assert result is False

    def test_delete_by_kb_success(self):
        """Test delete_by_kb when successful."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 3
        
        store = ExactCacheStore(redis_client=mock_redis)
        deleted = store.delete_by_kb(kb_id=1)
        
        assert deleted == 3
        mock_redis.keys.assert_called_once()
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    def test_delete_by_kb_no_keys(self):
        """Test delete_by_kb when no keys found."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        mock_redis.keys.return_value = []
        
        store = ExactCacheStore(redis_client=mock_redis)
        deleted = store.delete_by_kb(kb_id=1)
        
        assert deleted == 0
        mock_redis.delete.assert_not_called()

    def test_delete_by_kb_exception(self):
        """Test delete_by_kb when exception occurs."""
        from app.cache.query_cache import ExactCacheStore
        
        mock_redis = MagicMock()
        mock_redis.keys.side_effect = Exception("Redis error")
        
        store = ExactCacheStore(redis_client=mock_redis)
        deleted = store.delete_by_kb(kb_id=1)
        
        assert deleted == 0


class TestSemanticCacheMatcher:
    """Tests for SemanticCacheMatcher."""

    def test_semantic_matcher_init(self):
        """Test SemanticCacheMatcher initialization."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_embedding = MagicMock()
        
        matcher = SemanticCacheMatcher(
            redis_client=mock_redis,
            embedding_service=mock_embedding,
        )
        assert matcher._redis is mock_redis
        assert matcher._embedding_service is mock_embedding

    def test_semantic_matcher_redis_property_none(self):
        """Test redis property when _redis is None."""
        from app.cache.query_cache import SemanticCacheMatcher, get_redis_client
        
        with patch('app.cache.query_cache.get_redis_client') as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            
            matcher = SemanticCacheMatcher()
            assert matcher._redis is None
            assert matcher.redis is mock_redis
            assert matcher._redis is mock_redis

    def test_get_index_key(self):
        """Test _get_index_key method."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        matcher = SemanticCacheMatcher()
        key = matcher._get_index_key(kb_id=123)
        assert key == "qa:semantic:kb:123:index"

    def test_cosine_similarity(self):
        """Test _cosine_similarity method."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        matcher = SemanticCacheMatcher()
        
        # Mock numpy operations
        with patch('numpy.array') as mock_array, \
             patch('numpy.dot', return_value=0.8) as mock_dot, \
             patch('numpy.linalg.norm', return_value=1.0) as mock_norm:
            mock_array.return_value = MagicMock()
            result = matcher._cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
            assert isinstance(result, float)
            assert result == 0.8  # Mocked value

    def test_find_semantic_match_no_index(self):
        """Test find_semantic_match when no index exists."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            matcher = SemanticCacheMatcher(redis_client=mock_redis)
            result = matcher.find_semantic_match(kb_id=1, query="test")
            
            assert result is None

    def test_find_semantic_match_cache_disabled(self):
        """Test find_semantic_match when cache is disabled."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = False
            matcher = SemanticCacheMatcher(redis_client=mock_redis)
            result = matcher.find_semantic_match(kb_id=1, query="test")
            
            assert result is None
            mock_redis.get.assert_not_called()

    def test_find_semantic_match_no_queries(self):
        """Test find_semantic_match when index has no queries."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({"queries": []})
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            matcher = SemanticCacheMatcher(redis_client=mock_redis)
            result = matcher.find_semantic_match(kb_id=1, query="test")
            
            assert result is None

    def test_find_semantic_match_below_threshold(self):
        """Test find_semantic_match when best match is below threshold."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({
            "queries": [{
                "query": "similar query",
                "embedding": [0.1, 0.2],
                "data": {"answer": "test"},
            }]
        })
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            mock_settings.cache_semantic_threshold = 0.9
            
            matcher = SemanticCacheMatcher(redis_client=mock_redis)
            
            # Mock numpy operations
            with patch('numpy.array') as mock_array, \
                 patch('numpy.dot', return_value=0.8) as mock_dot, \
                 patch('numpy.linalg.norm', return_value=1.0) as mock_norm:
                mock_array.return_value = MagicMock()
                result = matcher.find_semantic_match(kb_id=1, query="test query")
                
                assert result is None  # Mocked similarity 0.8 < 0.9 threshold

    def test_find_semantic_match_above_threshold(self):
        """Test find_semantic_match when best match is above threshold."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({
            "queries": [{
                "query": "similar query",
                "embedding": [0.1, 0.2],
                "data": {"answer": "test answer"},
            }]
        })
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            mock_settings.cache_semantic_threshold = 0.7
            
            matcher = SemanticCacheMatcher(redis_client=mock_redis)
            
            # Mock numpy operations
            with patch('numpy.array') as mock_array, \
                 patch('numpy.dot', return_value=0.8) as mock_dot, \
                 patch('numpy.linalg.norm', return_value=1.0) as mock_norm:
                mock_array.return_value = MagicMock()
                result = matcher.find_semantic_match(kb_id=1, query="test query")
                
                assert result is not None
                assert result["answer"] == "test answer"
                assert result["cache_type"] == "semantic"
                assert result["similarity_score"] == 0.8

    def test_find_semantic_match_exception(self):
        """Test find_semantic_match when exception occurs."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis error")
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            matcher = SemanticCacheMatcher(redis_client=mock_redis)
            result = matcher.find_semantic_match(kb_id=1, query="test")
            
            assert result is None

    def test_add_to_index_new_index(self):
        """Test add_to_index creating new index."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            mock_settings.cache_default_ttl_seconds = 3600
            mock_settings.cache_max_entries_per_kb = 100
            
            matcher = SemanticCacheMatcher(
                redis_client=mock_redis,
                embedding_service=mock_embedding,
            )
            result = matcher.add_to_index(kb_id=1, query="test", data={"answer": "test"})
            
            assert result is True
            mock_redis.get.assert_called_once()
            mock_redis.setex.assert_called_once()
            
            # Verify data structure
            call_args = mock_redis.setex.call_args
            saved_data = json.loads(call_args[0][2])
            assert len(saved_data["queries"]) == 1
            assert saved_data["queries"][0]["query"] == "test"

    def test_add_to_index_existing_index(self):
        """Test add_to_index adding to existing index."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        existing_data = {"queries": [{"query": "old", "embedding": [], "data": {}}]}
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps(existing_data)
        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            mock_settings.cache_default_ttl_seconds = 3600
            mock_settings.cache_max_entries_per_kb = 100
            
            matcher = SemanticCacheMatcher(
                redis_client=mock_redis,
                embedding_service=mock_embedding,
            )
            result = matcher.add_to_index(kb_id=1, query="test", data={"answer": "test"})
            
            assert result is True
            
            # Verify data structure
            call_args = mock_redis.setex.call_args
            saved_data = json.loads(call_args[0][2])
            assert len(saved_data["queries"]) == 2  # old + new

    def test_add_to_index_max_entries(self):
        """Test add_to_index respects max entries limit."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        # Create 150 existing queries
        existing_queries = [
            {"query": f"q{i}", "embedding": [i], "data": {}}
            for i in range(150)
        ]
        existing_data = {"queries": existing_queries}
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps(existing_data)
        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            mock_settings.cache_default_ttl_seconds = 3600
            mock_settings.cache_max_entries_per_kb = 100
            
            matcher = SemanticCacheMatcher(
                redis_client=mock_redis,
                embedding_service=mock_embedding,
            )
            result = matcher.add_to_index(kb_id=1, query="test", data={})
            
            assert result is True
            
            # Verify truncated to 100
            call_args = mock_redis.setex.call_args
            saved_data = json.loads(call_args[0][2])
            assert len(saved_data["queries"]) == 100

    def test_add_to_index_cache_disabled(self):
        """Test add_to_index when cache is disabled."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_embedding = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = False
            matcher = SemanticCacheMatcher(
                redis_client=mock_redis,
                embedding_service=mock_embedding,
            )
            result = matcher.add_to_index(kb_id=1, query="test", data={})
            
            assert result is False
            mock_redis.get.assert_not_called()

    def test_add_to_index_exception(self):
        """Test add_to_index when exception occurs."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis error")
        mock_embedding = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            matcher = SemanticCacheMatcher(
                redis_client=mock_redis,
                embedding_service=mock_embedding,
            )
            result = matcher.add_to_index(kb_id=1, query="test", data={})
            
            assert result is False

    def test_delete_by_kb(self):
        """Test delete_by_kb method."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        matcher = SemanticCacheMatcher(redis_client=mock_redis)
        result = matcher.delete_by_kb(kb_id=1)
        
        assert result is True
        mock_redis.delete.assert_called_once()

    def test_delete_by_kb_exception(self):
        """Test delete_by_kb when exception occurs."""
        from app.cache.query_cache import SemanticCacheMatcher
        
        mock_redis = MagicMock()
        mock_redis.delete.side_effect = Exception("Redis error")
        matcher = SemanticCacheMatcher(redis_client=mock_redis)
        result = matcher.delete_by_kb(kb_id=1)
        
        assert result is False


class TestQueryCacheService:
    """Tests for QueryCacheService."""

    def test_cache_service_init(self):
        """Test QueryCacheService initialization."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_semantic = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            
            service = QueryCacheService(
                enabled=True,
                exact_store=mock_exact,
                semantic_matcher=mock_semantic,
            )
            assert service._enabled is True
            assert service._exact_store is mock_exact
            assert service._semantic_matcher is mock_semantic

    def test_cache_service_init_defaults(self):
        """Test QueryCacheService initialization with defaults."""
        from app.cache.query_cache import QueryCacheService, ExactCacheStore, SemanticCacheMatcher
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            
            service = QueryCacheService()
            assert service._enabled is True
            assert isinstance(service._exact_store, ExactCacheStore)
            assert isinstance(service._semantic_matcher, SemanticCacheMatcher)

    def test_get_exact_hit(self):
        """Test get when exact cache hits."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_exact.get.return_value = {"answer": "test"}
        mock_semantic = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            
            service = QueryCacheService(
                exact_store=mock_exact,
                semantic_matcher=mock_semantic,
            )
            result = service.get(kb_id=1, query="test")
            
            assert result == {"answer": "test", "cache_type": "exact"}
            mock_exact.get.assert_called_once_with(1, "test")
            mock_semantic.find_semantic_match.assert_not_called()

    def test_get_semantic_hit(self):
        """Test get when semantic cache hits."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_exact.get.return_value = None
        mock_semantic = MagicMock()
        mock_semantic.find_semantic_match.return_value = {
            "answer": "test",
            "similarity_score": 0.8,
        }
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            
            service = QueryCacheService(
                exact_store=mock_exact,
                semantic_matcher=mock_semantic,
            )
            result = service.get(kb_id=1, query="test")
            
            assert result["answer"] == "test"
            assert result["similarity_score"] == 0.8
            mock_exact.get.assert_called_once()
            mock_semantic.find_semantic_match.assert_called_once()

    def test_get_miss(self):
        """Test get when both caches miss."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_exact.get.return_value = None
        mock_semantic = MagicMock()
        mock_semantic.find_semantic_match.return_value = None
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            
            service = QueryCacheService(
                exact_store=mock_exact,
                semantic_matcher=mock_semantic,
            )
            result = service.get(kb_id=1, query="test")
            
            assert result is None

    def test_get_disabled(self):
        """Test get when cache is disabled."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_semantic = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = False
            
            service = QueryCacheService(
                enabled=False,
                exact_store=mock_exact,
                semantic_matcher=mock_semantic,
            )
            result = service.get(kb_id=1, query="test")
            
            assert result is None
            mock_exact.get.assert_not_called()
            mock_semantic.find_semantic_match.assert_not_called()

    def test_set(self):
        """Test set method."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_exact.set.return_value = True
        mock_semantic = MagicMock()
        mock_semantic.add_to_index.return_value = True
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            
            service = QueryCacheService(
                exact_store=mock_exact,
                semantic_matcher=mock_semantic,
            )
            result = service.set(kb_id=1, query="test", data={"answer": "test"})
            
            assert result is True
            mock_exact.set.assert_called_once()
            mock_semantic.add_to_index.assert_called_once()

    def test_set_with_ttl(self):
        """Test set method with custom TTL."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_semantic = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = True
            
            service = QueryCacheService(
                exact_store=mock_exact,
                semantic_matcher=mock_semantic,
            )
            service.set(kb_id=1, query="test", data={}, ttl_seconds=7200)
            
            mock_exact.set.assert_called_once_with(1, "test", {}, 7200)
            mock_semantic.add_to_index.assert_called_once_with(1, "test", {}, 7200)

    def test_set_disabled(self):
        """Test set when cache is disabled."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_semantic = MagicMock()
        
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.cache_enabled = False
            
            service = QueryCacheService(
                enabled=False,
                exact_store=mock_exact,
                semantic_matcher=mock_semantic,
            )
            result = service.set(kb_id=1, query="test", data={})
            
            assert result is False
            mock_exact.set.assert_not_called()
            mock_semantic.add_to_index.assert_not_called()

    def test_invalidate_kb(self):
        """Test invalidate_kb method."""
        from app.cache.query_cache import QueryCacheService
        
        mock_exact = MagicMock()
        mock_exact.delete_by_kb.return_value = 5
        mock_semantic = MagicMock()
        mock_semantic.delete_by_kb.return_value = True
        
        service = QueryCacheService(
            exact_store=mock_exact,
            semantic_matcher=mock_semantic,
        )
        service.invalidate_kb(kb_id=1)
        
        mock_exact.delete_by_kb.assert_called_once_with(1)
        mock_semantic.delete_by_kb.assert_called_once_with(1)


class TestCacheInvalidator:
    """Tests for CacheInvalidator."""

    def test_cache_invalidator_init(self):
        """Test CacheInvalidator initialization."""
        from app.cache.query_cache import CacheInvalidator, QueryCacheService
        
        mock_cache = MagicMock()
        invalidator = CacheInvalidator(cache_service=mock_cache)
        assert invalidator._cache_service is mock_cache

    def test_cache_invalidator_init_default(self):
        """Test CacheInvalidator initialization with default cache service."""
        from app.cache.query_cache import CacheInvalidator
        
        with patch('app.cache.query_cache.QueryCacheService') as mock_cache_cls:
            mock_cache = MagicMock()
            mock_cache_cls.return_value = mock_cache
            
            invalidator = CacheInvalidator()
            assert invalidator._cache_service is mock_cache

    def test_on_document_change_add(self):
        """Test on_document_change with add action."""
        from app.cache.query_cache import CacheInvalidator
        
        mock_cache = MagicMock()
        invalidator = CacheInvalidator(cache_service=mock_cache)
        invalidator.on_document_change(kb_id=1, action="add")
        
        mock_cache.invalidate_kb.assert_called_once_with(1)

    def test_on_document_change_update(self):
        """Test on_document_change with update action."""
        from app.cache.query_cache import CacheInvalidator
        
        mock_cache = MagicMock()
        invalidator = CacheInvalidator(cache_service=mock_cache)
        invalidator.on_document_change(kb_id=1, action="update")
        
        mock_cache.invalidate_kb.assert_called_once_with(1)

    def test_on_document_change_delete(self):
        """Test on_document_change with delete action."""
        from app.cache.query_cache import CacheInvalidator
        
        mock_cache = MagicMock()
        invalidator = CacheInvalidator(cache_service=mock_cache)
        invalidator.on_document_change(kb_id=1, action="delete")
        
        mock_cache.invalidate_kb.assert_called_once_with(1)

    def test_on_document_change_other_action(self):
        """Test on_document_change with other action (no invalidate)."""
        from app.cache.query_cache import CacheInvalidator
        
        mock_cache = MagicMock()
        invalidator = CacheInvalidator(cache_service=mock_cache)
        invalidator.on_document_change(kb_id=1, action="read")
        
        mock_cache.invalidate_kb.assert_not_called()

    def test_on_chunk_change(self):
        """Test on_chunk_change method."""
        from app.cache.query_cache import CacheInvalidator
        
        mock_cache = MagicMock()
        invalidator = CacheInvalidator(cache_service=mock_cache)
        invalidator.on_chunk_change(kb_id=1)
        
        mock_cache.invalidate_kb.assert_called_once_with(1)

    def test_on_knowledge_base_delete(self):
        """Test on_knowledge_base_delete method."""
        from app.cache.query_cache import CacheInvalidator
        
        mock_cache = MagicMock()
        invalidator = CacheInvalidator(cache_service=mock_cache)
        invalidator.on_knowledge_base_delete(kb_id=1)
        
        mock_cache.invalidate_kb.assert_called_once_with(1)


class TestGetRedisClient:
    """Tests for get_redis_client function."""

    def test_get_redis_client_success(self):
        """Test get_redis_client when successful."""
        # Need to patch redis before the function runs
        import sys
        from unittest.mock import MagicMock
        
        mock_redis_module = MagicMock()
        mock_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_client
        
        # Patch redis in sys.modules
        sys.modules['redis'] = mock_redis_module
        
        # Patch settings
        from unittest.mock import patch
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            
            from app.cache.query_cache import get_redis_client
            result = get_redis_client()
            
            assert result is mock_client
            mock_redis_module.from_url.assert_called_once_with(
                "redis://localhost:6379",
                decode_responses=True
            )

    def test_get_redis_client_exception(self):
        """Test get_redis_client when exception occurs."""
        import sys
        from unittest.mock import MagicMock
        
        mock_redis_module = MagicMock()
        mock_redis_module.from_url.side_effect = Exception("Connection failed")
        
        # Patch redis in sys.modules
        sys.modules['redis'] = mock_redis_module
        
        # Patch settings
        from unittest.mock import patch
        with patch('app.cache.query_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            
            from app.cache.query_cache import get_redis_client
            result = get_redis_client()
            
            assert result is None
