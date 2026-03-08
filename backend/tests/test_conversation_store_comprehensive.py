"""
Unit tests for ConversationStore.

Tests for app/services/conversation_store.py
Author: C2
"""

import pytest
from unittest.mock import MagicMock, patch


class TestInMemoryConversationStore:
    """Tests for InMemoryConversationStore class."""

    def test_initialization(self):
        """Test store initialization."""
        from app.services.conversation_store import InMemoryConversationStore

        store = InMemoryConversationStore(max_turns=5)
        assert store._max_messages == 10  # 5 turns * 2 messages

    def test_get_messages_empty(self):
        """Test getting messages from empty store."""
        from app.services.conversation_store import InMemoryConversationStore

        store = InMemoryConversationStore()
        messages = store.get_messages("nonexistent-key")
        assert messages == []

    def test_append_messages_new_key(self):
        """Test appending messages to new key."""
        from app.services.conversation_store import InMemoryConversationStore

        store = InMemoryConversationStore()
        mock_messages = [
            MagicMock(role="user", content="Hello"),
            MagicMock(role="assistant", content="Hi!"),
        ]

        store.append_messages("test-key", mock_messages)
        messages = store.get_messages("test-key")
        assert len(messages) == 2

    def test_append_messages_existing_key(self):
        """Test appending messages to existing key."""
        from app.services.conversation_store import InMemoryConversationStore

        store = InMemoryConversationStore()
        mock_messages1 = [MagicMock(role="user", content="Hello")]
        mock_messages2 = [MagicMock(role="assistant", content="Hi!")]

        store.append_messages("test-key", mock_messages1)
        store.append_messages("test-key", mock_messages2)

        messages = store.get_messages("test-key")
        assert len(messages) == 2

    def test_append_messages_respects_max(self):
        """Test that max_messages is respected."""
        from app.services.conversation_store import InMemoryConversationStore

        store = InMemoryConversationStore(max_turns=2)  # max 4 messages

        # Add 6 messages
        for i in range(6):
            msg = MagicMock(role="user" if i % 2 == 0 else "assistant", content=f"msg{i}")
            store.append_messages("test-key", [msg])

        messages = store.get_messages("test-key")
        assert len(messages) == 4
        # Should keep most recent 4
        assert messages[0].content == "msg2"

    def test_clear_existing_key(self):
        """Test clearing existing key."""
        from app.services.conversation_store import InMemoryConversationStore

        store = InMemoryConversationStore()
        mock_messages = [MagicMock(role="user", content="Hello")]

        store.append_messages("test-key", mock_messages)
        store.clear("test-key")

        messages = store.get_messages("test-key")
        assert messages == []

    def test_clear_nonexistent_key(self):
        """Test clearing nonexistent key does not raise."""
        from app.services.conversation_store import InMemoryConversationStore

        store = InMemoryConversationStore()
        store.clear("nonexistent-key")  # Should not raise


class TestRedisConversationStore:
    """Tests for RedisConversationStore class."""

    def test_initialization(self):
        """Test Redis store initialization."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            assert store._max_messages == 20  # default 10 turns * 2

    def test_get_messages_empty(self):
        """Test getting messages when key doesn't exist."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            messages = store.get_messages("nonexistent-key")
            assert messages == []

    def test_get_messages_with_data(self):
        """Test getting messages with data."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        mock_redis.get.return_value = '[{"role": "user", "content": "Hello"}]'

        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            messages = store.get_messages("test-key")
            assert len(messages) == 1
            assert messages[0].role == "user"
            assert messages[0].content == "Hello"

    def test_append_messages_new_key(self):
        """Test appending messages to new key."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            mock_messages = [MagicMock(role="user", content="Hello")]
            store.append_messages("test-key", mock_messages)

            mock_redis.setex.assert_called_once()

    def test_append_messages_existing_key(self):
        """Test appending messages to existing key."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        mock_redis.get.return_value = '[{"role": "user", "content": "First"}]'

        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            mock_messages = [MagicMock(role="assistant", content="Second")]
            store.append_messages("test-key", mock_messages)

            # setex should be called with combined messages
            mock_redis.setex.assert_called_once()

    def test_append_messages_respects_max(self):
        """Test that max_messages is respected."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        # Return 5 existing messages
        mock_redis.get.return_value = '[{"role": "user", "content": "m0"}, {"role": "assistant", "content": "m1"}, {"role": "user", "content": "m2"}, {"role": "assistant", "content": "m3"}, {"role": "user", "content": "m4"}]'

        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379", max_turns=2)  # max 4 messages
            mock_messages = [MagicMock(role="assistant", content="m5")]
            store.append_messages("test-key", mock_messages)

            # Should have truncated to 4 messages
            call_args = mock_redis.setex.call_args
            serialized = call_args[0][2]
            assert '"m5"' in serialized  # New message should be there

    def test_clear(self):
        """Test clearing key."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()

        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            store.clear("test-key")

            mock_redis.delete.assert_called_once_with("conv:test-key")

    def test_serialize_messages(self):
        """Test message serialization."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            messages = [
                MagicMock(role="user", content="Hello"),
                MagicMock(role="assistant", content="Hi!"),
            ]
            serialized = store._serialize_messages(messages)

            assert '"role": "user"' in serialized
            assert '"content": "Hello"' in serialized

    def test_deserialize_messages_empty(self):
        """Test deserializing empty data."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            messages = store._deserialize_messages(None)
            assert messages == []

    def test_deserialize_messages_with_data(self):
        """Test deserializing with data."""
        from app.services.conversation_store import RedisConversationStore

        mock_redis = MagicMock()
        with patch("redis.from_url", return_value=mock_redis):
            store = RedisConversationStore("redis://localhost:6379")
            data = '[{"role": "user", "content": "Hello"}]'
            messages = store._deserialize_messages(data)

            assert len(messages) == 1
            assert messages[0].role == "user"

    def test_import_error_without_redis(self):
        """Test that ImportError is raised when redis not installed."""
        from app.services.conversation_store import RedisConversationStore

        with patch.dict("sys.modules", {"redis": None}):
            with pytest.raises(ImportError) as exc_info:
                RedisConversationStore("redis://localhost:6379")
            assert "redis" in str(exc_info.value).lower()


class TestCreateConversationStore:
    """Tests for create_conversation_store factory function."""

    def test_creates_in_memory_when_no_redis_url(self):
        """Test creates in-memory store when no Redis URL."""
        from app.services.conversation_store import (
            create_conversation_store,
            InMemoryConversationStore,
        )

        mock_settings = MagicMock()
        mock_settings.redis_url = None
        mock_settings.qa_history_max_turns = 10

        with patch("app.services.conversation_store.settings", mock_settings):
            store = create_conversation_store()
            assert isinstance(store, InMemoryConversationStore)

    def test_creates_redis_when_url_configured(self):
        """Test creates Redis store when URL is configured."""
        from app.services.conversation_store import (
            create_conversation_store,
            RedisConversationStore,
            InMemoryConversationStore,
        )

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.qa_history_max_turns = 10

        mock_redis = MagicMock()
        with patch("app.services.conversation_store.settings", mock_settings):
            with patch("redis.from_url", return_value=mock_redis):
                store = create_conversation_store()
                assert isinstance(store, RedisConversationStore)

    def test_fallback_to_memory_on_redis_error(self):
        """Test falls back to in-memory on Redis error."""
        from app.services.conversation_store import (
            create_conversation_store,
            InMemoryConversationStore,
        )

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.qa_history_max_turns = 10

        with patch("app.services.conversation_store.settings", mock_settings):
            with patch("redis.from_url", side_effect=Exception("Redis error")):
                store = create_conversation_store()
                assert isinstance(store, InMemoryConversationStore)


class TestGetConversationStore:
    """Tests for get_conversation_store singleton."""

    def test_returns_singleton(self):
        """Test that get_conversation_store returns singleton."""
        from app.services.conversation_store import (
            get_conversation_store,
            _conversation_store,
        )
        import app.services.conversation_store as module

        # Reset singleton
        module._conversation_store = None

        store1 = get_conversation_store()
        store2 = get_conversation_store()

        assert store1 is store2

        # Clean up
        module._conversation_store = None
