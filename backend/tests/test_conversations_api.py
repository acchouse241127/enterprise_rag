"""
Unit tests for Conversations API endpoints.

Tests for app/api/conversations.py
Author: C2
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.conversations import (
    ConversationCreate,
    MessageCreate,
    ShareSettings,
    ConversationResponse,
    MessageResponse,
)


class TestSchemas:
    """Tests for schema validation."""

    def test_conversation_create_validation(self):
        """Test ConversationCreate schema validation."""
        # Valid with title
        data = ConversationCreate(knowledge_base_id=1, title="Test")
        assert data.knowledge_base_id == 1
        assert data.title == "Test"

        # Valid without title
        data = ConversationCreate(knowledge_base_id=1)
        assert data.knowledge_base_id == 1
        assert data.title is None

    def test_message_create_validation(self):
        """Test MessageCreate schema validation."""
        data = MessageCreate(role="user", content="Hello")
        assert data.role == "user"
        assert data.content == "Hello"
        assert data.extra_data is None

        data = MessageCreate(role="assistant", content="Hi!", extra_data={"key": "value"})
        assert data.extra_data == {"key": "value"}

    def test_share_settings_validation(self):
        """Test ShareSettings schema validation."""
        data = ShareSettings()
        assert data.expires_in_days == 7

        data = ShareSettings(expires_in_days=30)
        assert data.expires_in_days == 30

        data = ShareSettings(expires_in_days=None)
        assert data.expires_in_days is None

    def test_conversation_response_schema(self):
        """Test ConversationResponse schema."""
        data = ConversationResponse(
            id=1,
            conversation_id="conv-123",
            knowledge_base_id=1,
            title="Test",
            is_shared=False,
            share_token=None,
            share_expires_at=None,
            user_id=1,
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T00:00:00",
        )
        assert data.id == 1
        assert data.conversation_id == "conv-123"

    def test_message_response_schema(self):
        """Test MessageResponse schema."""
        data = MessageResponse(
            id=1,
            role="user",
            content="Hello",
            extra_data=None,
            created_at="2026-01-01T00:00:00",
        )
        assert data.id == 1
        assert data.role == "user"


class TestConversationEndpointLogic:
    """Tests for conversation endpoint logic (isolated from FastAPI)."""

    def test_create_conversation_calls_service(self):
        """Test that create_conversation endpoint calls service correctly."""
        from app.api.conversations import create_conversation

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.conversation_id = "conv-123"
        mock_conv.knowledge_base_id = 1
        mock_conv.title = "Test"
        mock_conv.is_shared = False
        mock_conv.share_token = None
        mock_conv.share_expires_at = None
        mock_conv.user_id = 1
        mock_conv.created_at = datetime.now()
        mock_conv.updated_at = datetime.now()

        with patch("app.api.conversations.ConversationService.create_conversation", return_value=mock_conv):
            data = ConversationCreate(knowledge_base_id=1, title="Test")
            result = create_conversation(data, mock_db, mock_user)

            assert result.id == 1

    def test_get_conversation_not_found_raises(self):
        """Test get_conversation raises 404 when not found."""
        from app.api.conversations import get_conversation
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_conversation(999, mock_db, mock_user)
            assert exc_info.value.status_code == 404

    def test_get_conversation_forbidden_raises(self):
        """Test get_conversation raises 403 when forbidden."""
        from app.api.conversations import get_conversation
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_user = MagicMock(id=1, role="user")

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 999  # Different user
        mock_conv.conversation_id = "conv-123"
        mock_conv.knowledge_base_id = 1
        mock_conv.title = "Test"
        mock_conv.is_shared = False
        mock_conv.share_token = None
        mock_conv.share_expires_at = None
        mock_conv.created_at = datetime.now()
        mock_conv.updated_at = datetime.now()

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with pytest.raises(HTTPException) as exc_info:
                get_conversation(1, mock_db, mock_user)
            assert exc_info.value.status_code == 403

    def test_get_conversation_admin_allowed(self):
        """Test admin can access any conversation."""
        from app.api.conversations import get_conversation

        mock_db = MagicMock()
        mock_admin = MagicMock(id=2, role="admin")

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 999  # Different user
        mock_conv.conversation_id = "conv-123"
        mock_conv.knowledge_base_id = 1
        mock_conv.title = "Test"
        mock_conv.is_shared = False
        mock_conv.share_token = None
        mock_conv.share_expires_at = None
        mock_conv.created_at = datetime.now()
        mock_conv.updated_at = datetime.now()

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            result = get_conversation(1, mock_db, mock_admin)
            assert result.id == 1

    def test_add_message_calls_service(self):
        """Test add_message calls service correctly."""
        from app.api.conversations import add_message

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1

        mock_msg = MagicMock()
        mock_msg.id = 1
        mock_msg.role = "user"
        mock_msg.content = "Hello"
        mock_msg.extra_data = None
        mock_msg.created_at = datetime.now()

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.add_message", return_value=mock_msg):
                data = MessageCreate(role="user", content="Hello")
                result = add_message(1, data, mock_db, mock_user)
                assert result.id == 1

    def test_get_messages_returns_list(self):
        """Test get_messages returns message list."""
        from app.api.conversations import get_messages

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1

        mock_msg = MagicMock()
        mock_msg.id = 1
        mock_msg.role = "user"
        mock_msg.content = "Hello"
        mock_msg.extra_data = None
        mock_msg.created_at = datetime.now()

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.get_messages", return_value=[mock_msg]):
                result = get_messages(1, mock_db, mock_user)
                assert len(result) == 1

    def test_enable_sharing_calls_service(self):
        """Test enable_sharing calls service correctly."""
        from app.api.conversations import enable_sharing

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1
        mock_conv.share_expires_at = datetime.now()

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.enable_sharing", return_value=(mock_conv, "token123")):
                settings = ShareSettings(expires_in_days=7)
                result = enable_sharing(1, settings, mock_db, mock_user)
                assert result["share_token"] == "token123"

    def test_disable_sharing_calls_service(self):
        """Test disable_sharing calls service correctly."""
        from app.api.conversations import disable_sharing

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.disable_sharing"):
                result = disable_sharing(1, mock_db, mock_user)
                assert result["message"] == "分享已关闭"

    def test_delete_conversation_calls_service(self):
        """Test delete_conversation calls service correctly."""
        from app.api.conversations import delete_conversation

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.delete_conversation"):
                result = delete_conversation(1, mock_db, mock_user)
                assert result["message"] == "对话已删除"

    def test_export_markdown_returns_content(self):
        """Test export_markdown returns content."""
        from app.api.conversations import export_markdown

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1
        mock_conv.conversation_id = "conv-123-456"

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.export_to_markdown", return_value="# Title\nContent"):
                result = export_markdown(1, mock_db, mock_user)
                assert result.status_code == 200
                assert "attachment" in result.headers.get("content-disposition", "")

    def test_export_markdown_failed_raises(self):
        """Test export_markdown raises on failure."""
        from app.api.conversations import export_markdown
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.export_to_markdown", return_value=None):
                with pytest.raises(HTTPException) as exc_info:
                    export_markdown(1, mock_db, mock_user)
                assert exc_info.value.status_code == 500

    def test_export_pdf_returns_content(self):
        """Test export_pdf returns content."""
        from app.api.conversations import export_pdf

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1
        mock_conv.conversation_id = "conv-123-456"

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.export_to_pdf_bytes", return_value=b"pdf content"):
                result = export_pdf(1, mock_db, mock_user)
                assert result.status_code == 200
                assert result.media_type == "application/pdf"

    def test_export_docx_returns_content(self):
        """Test export_docx returns content."""
        from app.api.conversations import export_docx

        mock_db = MagicMock()
        mock_user = MagicMock(id=1)

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user_id = 1
        mock_conv.conversation_id = "conv-123-456"

        with patch("app.api.conversations.ConversationService.get_conversation", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.export_to_docx_bytes", return_value=b"docx content"):
                result = export_docx(1, mock_db, mock_user)
                assert result.status_code == 200

    def test_get_shared_conversation_success(self):
        """Test get_shared_conversation returns shared data."""
        from app.api.conversations import get_shared_conversation

        mock_db = MagicMock()

        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.conversation_id = "conv-123"
        mock_conv.title = "Shared"
        mock_conv.knowledge_base_id = 1
        mock_conv.created_at = datetime.now()

        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_msg.content = "Hello"
        mock_msg.created_at = datetime.now()

        with patch("app.api.conversations.ConversationService.get_by_share_token", return_value=mock_conv):
            with patch("app.api.conversations.ConversationService.get_messages", return_value=[mock_msg]):
                with patch("app.services.knowledge_base_service.KnowledgeBaseService.get_by_id") as mock_kb:
                    mock_kb.return_value = MagicMock(name="KB1")
                    result = get_shared_conversation("token123", mock_db)
                    assert result["code"] == 0
                    assert result["data"]["title"] == "Shared"

    def test_get_shared_conversation_invalid_token(self):
        """Test get_shared_conversation with invalid token."""
        from app.api.conversations import get_shared_conversation
        from fastapi import HTTPException

        mock_db = MagicMock()

        with patch("app.api.conversations.ConversationService.get_by_share_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_shared_conversation("invalid", mock_db)
            assert exc_info.value.status_code == 404
