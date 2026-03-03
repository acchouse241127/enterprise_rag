"""
Conversation Service测试 - 目标覆盖 app/services/conversation_service.py (221语句)
从19%提升至80%+
"""
import pytest
from unittest.mock import Mock, AsyncMock

class TestConversationService:
    """测试对话服务"""

    @pytest.fixture
    def mock_conv_service(self):
        """Mock对话服务"""
        from app.services.conversation_service import ConversationService
        
        mock_db = Mock()
        service = ConversationService(db_session=mock_db)
        return service, mock_db

    def test_create_conversation(self, mock_conv_service):
        """测试创建对话"""
        service, mock_db = mock_conv_service
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        conversation = service.create_conversation(
            knowledge_base_id=1,
            user_id="user123",
            title="测试对话"
        )
        
        assert conversation.id is not None
        assert conversation.title == "测试对话"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_conversation_by_id(self, mock_conv_service):
        """测试通过ID获取对话"""
        service, mock_db = mock_conv_service
        
        mock_conv = Mock(id=1, title="对话1")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv
        
        result = service.get_conversation_by_id(1)
        
        assert result.id == 1
        assert result.title == "对话1"

    def test_list_conversations(self, mock_conv_service):
        """测试列出用户对话"""
        service, mock_db = mock_conv_service
        
        mock_convs = [Mock(id=i, title=f"对话{i}") for i in range(1, 4)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_convs
        
        result = service.list_conversations(user_id="user123")
        
        assert len(result) == 3
        assert result[0].id == 1

    def test_delete_conversation(self, mock_conv_service):
        """测试删除对话"""
        service, mock_db = mock_conv_service
        
        mock_conv = Mock(id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        result = service.delete_conversation(conversation_id=1)
        
        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_conversation_title(self, mock_conv_service):
        """测试更新对话标题"""
        service, mock_db = mock_conv_service
        
        mock_conv = Mock(id=1, title="旧标题")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv
        mock_db.commit = Mock()
        
        service.update_conversation_title(
            conversation_id=1,
            title="新标题"
        )
        
        assert mock_conv.title == "新标题"
        mock_db.commit.assert_called_once()
