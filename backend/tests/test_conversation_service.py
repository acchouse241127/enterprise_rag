"""
Unit tests for ConversationService.

Tests for app/services/conversation_service.py
Author: C2
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock


class TestConversationServiceCreate:
    """Tests for ConversationService.create_conversation."""

    def test_create_conversation_basic(self):
        """Test basic conversation creation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.conversation_id = "test-uuid"

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Mock the Conversation constructor
        with patch("app.services.conversation_service.Conversation") as MockConv:
            MockConv.return_value = mock_conv
            result = ConversationService.create_conversation(
                db=mock_db,
                knowledge_base_id=1,
                user_id=1,
                title="Test Chat"
            )
            assert result is not None
            MockConv.assert_called_once()

    def test_create_conversation_with_custom_id(self):
        """Test conversation creation with custom conversation_id."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        custom_id = "custom-conversation-123"

        with patch("app.services.conversation_service.Conversation") as MockConv:
            MockConv.return_value = mock_conv
            ConversationService.create_conversation(
                db=mock_db,
                knowledge_base_id=1,
                conversation_id=custom_id
            )
            # Verify custom_id was used (after strip)
            call_kwargs = MockConv.call_args[1]
            assert call_kwargs["conversation_id"] == custom_id

    def test_create_conversation_strips_whitespace_from_id(self):
        """Test that whitespace is stripped from conversation_id."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()

        with patch("app.services.conversation_service.Conversation") as MockConv:
            MockConv.return_value = mock_conv
            ConversationService.create_conversation(
                db=mock_db,
                knowledge_base_id=1,
                conversation_id="  spaced-id  "
            )
            call_kwargs = MockConv.call_args[1]
            assert call_kwargs["conversation_id"] == "spaced-id"


class TestConversationServiceGet:
    """Tests for ConversationService get methods."""

    def test_get_conversation_by_id(self):
        """Test getting conversation by numeric ID."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_result.scalar_one_or_none.return_value = mock_conv

        mock_db.execute.return_value = mock_result

        result = ConversationService.get_conversation(mock_db, 1)
        assert result == mock_conv

    def test_get_conversation_by_id_not_found(self):
        """Test getting non-existent conversation returns None."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_result

        result = ConversationService.get_conversation(mock_db, 999)
        assert result is None

    def test_get_by_conversation_id(self):
        """Test getting conversation by UUID string."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_conv = MagicMock()
        mock_conv.conversation_id = "test-uuid-123"
        mock_result.scalar_one_or_none.return_value = mock_conv

        mock_db.execute.return_value = mock_result

        result = ConversationService.get_by_conversation_id(mock_db, "test-uuid-123")
        assert result == mock_conv

    def test_get_by_share_token_valid(self):
        """Test getting conversation by valid share token."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_conv = MagicMock()
        mock_conv.is_shared = True
        mock_conv.share_expires_at = datetime.now() + timedelta(days=1)
        mock_result.scalar_one_or_none.return_value = mock_conv

        mock_db.execute.return_value = mock_result

        result = ConversationService.get_by_share_token(mock_db, "share-token-123")
        assert result == mock_conv

    def test_get_by_share_token_not_shared(self):
        """Test getting conversation by share token when not shared."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_conv = MagicMock()
        mock_conv.is_shared = False
        mock_result.scalar_one_or_none.return_value = mock_conv

        mock_db.execute.return_value = mock_result

        result = ConversationService.get_by_share_token(mock_db, "share-token-123")
        assert result is None

    def test_get_by_share_token_expired(self):
        """Test getting conversation by expired share token."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_conv = MagicMock()
        mock_conv.is_shared = True
        mock_conv.share_expires_at = datetime.now() - timedelta(days=1)  # Expired
        mock_result.scalar_one_or_none.return_value = mock_conv

        mock_db.execute.return_value = mock_result

        result = ConversationService.get_by_share_token(mock_db, "share-token-123")
        assert result is None

    def test_get_by_share_token_not_found(self):
        """Test getting conversation by non-existent share token."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_result

        result = ConversationService.get_by_share_token(mock_db, "invalid-token")
        assert result is None


class TestConversationServiceList:
    """Tests for ConversationService.list_conversations."""

    def test_list_conversations_no_filters(self):
        """Test listing conversations without filters."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_convs = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_convs
        mock_db.execute.return_value = mock_result

        result = ConversationService.list_conversations(mock_db)
        assert len(result) == 2

    def test_list_conversations_with_user_filter(self):
        """Test listing conversations filtered by user."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_convs = [MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_convs
        mock_db.execute.return_value = mock_result

        result = ConversationService.list_conversations(mock_db, user_id=1)
        assert len(result) == 1

    def test_list_conversations_with_kb_filter(self):
        """Test listing conversations filtered by knowledge base."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_convs = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_convs
        mock_db.execute.return_value = mock_result

        result = ConversationService.list_conversations(mock_db, knowledge_base_id=5)
        assert len(result) == 2

    def test_list_conversations_with_pagination(self):
        """Test listing conversations with limit and offset."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = ConversationService.list_conversations(mock_db, limit=10, offset=5)
        assert result == []


class TestConversationServiceAddMessage:
    """Tests for ConversationService.add_message."""

    def test_add_message_user(self):
        """Test adding user message."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.id = 1

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            with patch("app.services.conversation_service.ConversationMessage") as MockMsg:
                mock_msg = MagicMock()
                MockMsg.return_value = mock_msg

                result = ConversationService.add_message(
                    mock_db, 1, "user", "Hello world"
                )
                assert result == mock_msg
                mock_db.add.assert_called()
                mock_db.commit.assert_called()

    def test_add_message_assistant(self):
        """Test adding assistant message."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.id = 1

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            with patch("app.services.conversation_service.ConversationMessage") as MockMsg:
                mock_msg = MagicMock()
                MockMsg.return_value = mock_msg

                result = ConversationService.add_message(
                    mock_db, 1, "assistant", "Hello! How can I help?"
                )
                assert result == mock_msg

    def test_add_message_with_extra_data(self):
        """Test adding message with extra data (citations)."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.id = 1

        extra_data = {"citations": [{"document_title": "Doc1"}]}

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            with patch("app.services.conversation_service.ConversationMessage") as MockMsg:
                mock_msg = MagicMock()
                MockMsg.return_value = mock_msg

                result = ConversationService.add_message(
                    mock_db, 1, "assistant", "Answer", extra_data=extra_data
                )
                assert result == mock_msg


class TestConversationServiceSharing:
    """Tests for ConversationService sharing methods."""

    def test_enable_sharing(self):
        """Test enabling conversation sharing."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.share_token = None

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            with patch("app.services.conversation_service.Conversation.generate_share_token", return_value="new-token"):
                result, token = ConversationService.enable_sharing(mock_db, 1)
                assert token == "new-token"
                mock_db.commit.assert_called()

    def test_enable_sharing_with_existing_token(self):
        """Test enabling sharing when token already exists."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.share_token = "existing-token"

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            result, token = ConversationService.enable_sharing(mock_db, 1)
            assert token == "existing-token"

    def test_enable_sharing_with_expiration(self):
        """Test enabling sharing with custom expiration."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.share_token = "test-token"

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            ConversationService.enable_sharing(mock_db, 1, expires_in_days=3)
            assert mock_conv.share_expires_at is not None

    def test_enable_sharing_no_expiration(self):
        """Test enabling sharing without expiration."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.share_token = "test-token"

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            ConversationService.enable_sharing(mock_db, 1, expires_in_days=None)
            assert mock_conv.share_expires_at is None

    def test_enable_sharing_conversation_not_found(self):
        """Test enabling sharing for non-existent conversation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()

        with patch.object(ConversationService, "get_conversation", return_value=None):
            result, token = ConversationService.enable_sharing(mock_db, 999)
            assert result is None
            assert token is None

    def test_disable_sharing(self):
        """Test disabling conversation sharing."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            result = ConversationService.disable_sharing(mock_db, 1)
            assert result == mock_conv
            assert mock_conv.is_shared == False
            mock_db.commit.assert_called()

    def test_disable_sharing_not_found(self):
        """Test disabling sharing for non-existent conversation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()

        with patch.object(ConversationService, "get_conversation", return_value=None):
            result = ConversationService.disable_sharing(mock_db, 999)
            assert result is None


class TestConversationServiceExport:
    """Tests for ConversationService export methods."""

    def test_export_to_markdown(self):
        """Test exporting conversation to Markdown."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.title = "Test Chat"
        mock_conv.conversation_id = "conv-123"

        mock_messages = [
            MagicMock(role="user", content="Hello", extra_data=None),
            MagicMock(role="assistant", content="Hi!", extra_data=None),
        ]

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            with patch.object(ConversationService, "get_messages", return_value=mock_messages):
                result = ConversationService.export_to_markdown(mock_db, 1)
                assert result is not None
                assert "# Test Chat" in result
                assert "Hello" in result
                assert "Hi!" in result

    def test_export_to_markdown_with_citations(self):
        """Test exporting with citations in extra_data."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.title = "Cited Chat"
        mock_conv.conversation_id = "conv-456"

        mock_messages = [
            MagicMock(
                role="assistant",
                content="See document",
                extra_data={"citations": [{"document_title": "Doc1.pdf"}]}
            ),
        ]

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            with patch.object(ConversationService, "get_messages", return_value=mock_messages):
                result = ConversationService.export_to_markdown(mock_db, 1)
                assert "引用来源" in result or "Doc1" in result

    def test_export_to_markdown_not_found(self):
        """Test exporting non-existent conversation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()

        with patch.object(ConversationService, "get_conversation", return_value=None):
            result = ConversationService.export_to_markdown(mock_db, 999)
            assert result is None


class TestConversationServiceUpdateTitle:
    """Tests for ConversationService.update_title."""

    def test_update_title(self):
        """Test updating conversation title."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            result = ConversationService.update_title(mock_db, 1, "New Title")
            assert result == mock_conv
            assert mock_conv.title == "New Title"
            mock_db.commit.assert_called()

    def test_update_title_not_found(self):
        """Test updating title for non-existent conversation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()

        with patch.object(ConversationService, "get_conversation", return_value=None):
            result = ConversationService.update_title(mock_db, 999, "Title")
            assert result is None


class TestConversationServiceDelete:
    """Tests for ConversationService.delete_conversation."""

    def test_delete_conversation(self):
        """Test deleting conversation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()

        with patch.object(ConversationService, "get_conversation", return_value=mock_conv):
            result = ConversationService.delete_conversation(mock_db, 1)
            assert result == True
            mock_db.delete.assert_called()
            mock_db.commit.assert_called()

    def test_delete_conversation_not_found(self):
        """Test deleting non-existent conversation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()

        with patch.object(ConversationService, "get_conversation", return_value=None):
            result = ConversationService.delete_conversation(mock_db, 999)
            assert result == False


class TestConversationServicePersistQaTurn:
    """Tests for ConversationService.persist_qa_turn."""

    def test_persist_qa_turn_new_conversation(self):
        """Test persisting QA turn creates new conversation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()

        with patch.object(ConversationService, "get_by_conversation_id", return_value=None):
            with patch.object(ConversationService, "create_conversation") as mock_create:
                mock_conv = MagicMock()
                mock_conv.id = 1
                mock_create.return_value = mock_conv

                with patch.object(ConversationService, "add_message") as mock_add:
                    ConversationService.persist_qa_turn(
                        mock_db, "new-conv-id", 1, None, "Question?", "Answer!"
                    )
                    mock_create.assert_called_once()
                    assert mock_add.call_count == 2

    def test_persist_qa_turn_existing_conversation(self):
        """Test persisting QA turn to existing conversation."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.id = 1

        with patch.object(ConversationService, "get_by_conversation_id", return_value=mock_conv):
            with patch.object(ConversationService, "add_message") as mock_add:
                ConversationService.persist_qa_turn(
                    mock_db, "existing-conv-id", 1, 1, "Q", "A"
                )
                assert mock_add.call_count == 2

    def test_persist_qa_turn_empty_conversation_id(self):
        """Test persisting with empty conversation ID does nothing."""
        from app.services.conversation_service import ConversationService

        mock_db = MagicMock()

        ConversationService.persist_qa_turn(mock_db, "", 1, None, "Q", "A")
        ConversationService.persist_qa_turn(mock_db, "   ", 1, None, "Q", "A")
        # Should not raise and should not call db methods
        mock_db.add.assert_not_called()
