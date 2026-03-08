"""Conversation history storage with pluggable backends.

Provides an abstraction for storing conversation history, supporting:
- InMemoryStore: Single-instance deployment (default)
- RedisStore: Multi-instance deployment with shared state
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from app.llm import ChatMessage

logger = logging.getLogger(__name__)


class ConversationStore(ABC):
    """Abstract base class for conversation history storage."""

    @abstractmethod
    def get_messages(self, key: str) -> list[ChatMessage]:
        """Get all messages for a conversation key."""
        pass

    @abstractmethod
    def append_messages(self, key: str, messages: list[ChatMessage]) -> None:
        """Append messages to a conversation."""
        pass

    @abstractmethod
    def clear(self, key: str) -> None:
        """Clear conversation history for a key."""
        pass


class InMemoryConversationStore(ConversationStore):
    """In-memory conversation store for single-instance deployment.

    Warning: State is lost on process restart and not shared across instances.
    """

    def __init__(self, max_turns: int = 10):
        self._store: dict[str, list[ChatMessage]] = {}
        self._max_messages = max_turns * 2  # Each turn = user + assistant

    def get_messages(self, key: str) -> list[ChatMessage]:
        return self._store.get(key, [])

    def append_messages(self, key: str, messages: list[ChatMessage]) -> None:
        if key not in self._store:
            self._store[key] = []
        self._store[key].extend(messages)
        # Keep only the most recent messages
        if len(self._store[key]) > self._max_messages:
            self._store[key] = self._store[key][-self._max_messages :]

    def clear(self, key: str) -> None:
        if key in self._store:
            del self._store[key]


class RedisConversationStore(ConversationStore):
    """Redis-backed conversation store for multi-instance deployment.

    Requires REDIS_URL environment variable.
    """

    def __init__(
        self,
        redis_url: str,
        max_turns: int = 10,
        ttl_seconds: int = 86400,
    ):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redis support requires 'redis' package. "
                "Install with: pip install redis"
            )

        self._client = redis.from_url(redis_url)
        self._max_messages = max_turns * 2
        self._ttl = ttl_seconds

    def _serialize_messages(self, messages: list[ChatMessage]) -> str:
        import json

        return json.dumps([
            {"role": m.role, "content": m.content} for m in messages
        ])

    def _deserialize_messages(self, data: str | None) -> list[ChatMessage]:
        if not data:
            return []
        import json

        from app.llm import ChatMessage

        items = json.loads(data)
        return [ChatMessage(role=i["role"], content=i["content"]) for i in items]

    def get_messages(self, key: str) -> list[ChatMessage]:
        data = self._client.get(f"conv:{key}")
        return self._deserialize_messages(data)

    def append_messages(self, key: str, messages: list[ChatMessage]) -> None:
        redis_key = f"conv:{key}"
        existing = self.get_messages(key)
        combined = existing + messages
        # Keep only the most recent messages
        if len(combined) > self._max_messages:
            combined = combined[-self._max_messages :]
        self._client.setex(
            redis_key,
            self._ttl,
            self._serialize_messages(combined),
        )

    def clear(self, key: str) -> None:
        self._client.delete(f"conv:{key}")


def create_conversation_store() -> ConversationStore:
    """Factory function to create the appropriate conversation store.

    Uses Redis if REDIS_URL is configured, otherwise falls back to in-memory.
    """
    redis_url = getattr(settings, "redis_url", None)
    if redis_url:
        try:
            store = RedisConversationStore(
                redis_url=redis_url,
                max_turns=settings.qa_history_max_turns,
            )
            logger.info("Using Redis conversation store")
            return store
        except Exception as e:
            logger.warning(
                "Failed to initialize Redis conversation store, falling back to memory: %s",
                e,
            )

    return InMemoryConversationStore(max_turns=settings.qa_history_max_turns)


# Singleton instance
_conversation_store: ConversationStore | None = None


def get_conversation_store() -> ConversationStore:
    """Get or create the singleton conversation store."""
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = create_conversation_store()
    return _conversation_store
