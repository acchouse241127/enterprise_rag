"""Query cache service for caching QA results.

Implements two-layer caching:
1. L1: Exact match cache (Redis) - fast, deterministic
2. L2: Semantic match cache (Vector similarity) - handles paraphrased queries

Author: C2
Date: 2026-03-03
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


def get_redis_client():
    """Get Redis client (lazy import to avoid startup issues)."""
    try:
        import redis

        return redis.from_url(settings.redis_url, decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        return None


class ExactCacheStore:
    """Redis-based exact match cache store."""

    KEY_PREFIX = "qa:cache:kb"

    def __init__(self, redis_client=None):
        self._redis = redis_client

    @property
    def redis(self):
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    def build_cache_key(self, kb_id: int, query: str) -> str:
        """Build cache key from knowledge base ID and query."""
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:32]
        return f"{self.KEY_PREFIX}:{kb_id}:query:{query_hash}"

    def get(self, kb_id: int, query: str) -> Optional[dict]:
        """Get cached result for exact query match."""
        if not settings.cache_enabled:
            return None

        try:
            key = self.build_cache_key(kb_id, query)
            cached = self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit (exact): kb={kb_id}, query={query[:50]}...")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        return None

    def set(
        self,
        kb_id: int,
        query: str,
        data: dict,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Set cache entry with TTL."""
        if not settings.cache_enabled:
            return False

        try:
            key = self.build_cache_key(kb_id, query)
            ttl = ttl_seconds or settings.cache_default_ttl_seconds
            self.redis.setex(key, ttl, json.dumps(data, ensure_ascii=False))
            logger.debug(f"Cache set: kb={kb_id}, query={query[:50]}..., ttl={ttl}")
            return True
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False

    def delete_by_kb(self, kb_id: int) -> int:
        """Delete all cache entries for a knowledge base."""
        try:
            pattern = f"{self.KEY_PREFIX}:{kb_id}:query:*"
            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Cache invalidated: kb={kb_id}, keys_deleted={deleted}")
                return deleted
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
        return 0


class SemanticCacheMatcher:
    """Semantic cache matcher using vector similarity."""

    KEY_PREFIX = "qa:semantic:kb"

    def __init__(self, redis_client=None, embedding_service=None):
        self._redis = redis_client
        self._embedding_service = embedding_service

    @property
    def redis(self):
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    def _get_index_key(self, kb_id: int) -> str:
        """Get key for semantic index."""
        return f"{self.KEY_PREFIX}:{kb_id}:index"

    def _get_embedding(self, query: str) -> list[float]:
        """Get embedding for query."""
        if self._embedding_service is None:
            # Lazy import to avoid circular dependency
            from app.rag import BgeM3EmbeddingService

            self._embedding_service = BgeM3EmbeddingService(
                model_name=settings.embedding_model_name,
                fallback_dim=settings.embedding_fallback_dim,
            )
        return self._embedding_service.embed(query)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

    def find_semantic_match(
        self,
        kb_id: int,
        query: str,
        threshold: Optional[float] = None,
    ) -> Optional[dict]:
        """Find semantically similar cached query."""
        if not settings.cache_enabled:
            return None

        threshold = threshold or settings.cache_semantic_threshold

        try:
            index_key = self._get_index_key(kb_id)
            cached = self.redis.get(index_key)
            if not cached:
                return None

            index_data = json.loads(cached)
            queries = index_data.get("queries", [])

            query_embedding = self._get_embedding(query)

            best_match = None
            best_score = 0.0

            for entry in queries:
                cached_embedding = entry.get("embedding", [])
                if not cached_embedding:
                    continue

                score = self._cosine_similarity(query_embedding, cached_embedding)
                if score >= threshold and score > best_score:
                    best_score = score
                    best_match = entry

            if best_match:
                logger.debug(
                    f"Cache hit (semantic): kb={kb_id}, score={best_score:.3f}, "
                    f"query={query[:50]}..., matched={best_match.get('query', '')[:50]}..."
                )
                result = best_match.get("data", {}).copy()
                result["cache_type"] = "semantic"
                result["similarity_score"] = best_score
                return result

        except Exception as e:
            logger.warning(f"Semantic cache search failed: {e}")

        return None

    def add_to_index(
        self,
        kb_id: int,
        query: str,
        data: dict,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Add query to semantic index."""
        if not settings.cache_enabled:
            return False

        try:
            index_key = self._get_index_key(kb_id)

            # Get existing index
            cached = self.redis.get(index_key)
            if cached:
                index_data = json.loads(cached)
            else:
                index_data = {"queries": []}

            # Get embedding for query
            query_embedding = self._get_embedding(query)

            # Add new entry
            entry = {
                "query": query,
                "embedding": query_embedding,
                "data": data,
            }
            index_data["queries"].append(entry)

            # Limit entries per KB
            max_entries = settings.cache_max_entries_per_kb
            if len(index_data["queries"]) > max_entries:
                index_data["queries"] = index_data["queries"][-max_entries:]

            # Save with TTL
            ttl = ttl_seconds or settings.cache_default_ttl_seconds
            self.redis.setex(index_key, ttl, json.dumps(index_data, ensure_ascii=False))
            logger.debug(f"Semantic index updated: kb={kb_id}, total_queries={len(index_data['queries'])}")
            return True

        except Exception as e:
            logger.warning(f"Semantic index update failed: {e}")
            return False

    def delete_by_kb(self, kb_id: int) -> bool:
        """Delete semantic index for a knowledge base."""
        try:
            index_key = self._get_index_key(kb_id)
            self.redis.delete(index_key)
            logger.info(f"Semantic cache invalidated: kb={kb_id}")
            return True
        except Exception as e:
            logger.warning(f"Semantic cache invalidation failed: {e}")
            return False


class QueryCacheService:
    """Main query cache service combining exact and semantic matching."""

    def __init__(
        self,
        enabled: Optional[bool] = None,
        exact_store: Optional[ExactCacheStore] = None,
        semantic_matcher: Optional[SemanticCacheMatcher] = None,
    ):
        self._enabled = enabled if enabled is not None else settings.cache_enabled
        self._exact_store = exact_store or ExactCacheStore()
        self._semantic_matcher = semantic_matcher or SemanticCacheMatcher()

    def get(self, kb_id: int, query: str) -> Optional[dict]:
        """Get cached result, trying exact match first, then semantic."""
        if not self._enabled:
            return None

        # Try exact match first (fast)
        result = self._exact_store.get(kb_id, query)
        if result is not None:
            result["cache_type"] = "exact"
            return result

        # Try semantic match (slower but handles paraphrases)
        result = self._semantic_matcher.find_semantic_match(kb_id, query)
        return result

    def set(
        self,
        kb_id: int,
        query: str,
        data: dict,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Cache result in both exact and semantic stores."""
        if not self._enabled:
            return False

        # Store in exact cache
        self._exact_store.set(kb_id, query, data, ttl_seconds)

        # Store in semantic index
        self._semantic_matcher.add_to_index(kb_id, query, data, ttl_seconds)

        return True

    def invalidate_kb(self, kb_id: int) -> None:
        """Invalidate all cache for a knowledge base."""
        self._exact_store.delete_by_kb(kb_id)
        self._semantic_matcher.delete_by_kb(kb_id)
        logger.info(f"Cache invalidated for kb={kb_id}")


class CacheInvalidator:
    """Helper class to invalidate cache on data changes."""

    def __init__(self, cache_service: Optional[QueryCacheService] = None):
        self._cache_service = cache_service or QueryCacheService()

    def on_document_change(self, kb_id: int, action: str) -> None:
        """Call when document is added/updated/deleted."""
        if action in ("add", "update", "delete"):
            self._cache_service.invalidate_kb(kb_id)

    def on_chunk_change(self, kb_id: int) -> None:
        """Call when chunks are changed."""
        self._cache_service.invalidate_kb(kb_id)

    def on_knowledge_base_delete(self, kb_id: int) -> None:
        """Call when knowledge base is deleted."""
        self._cache_service.invalidate_kb(kb_id)
