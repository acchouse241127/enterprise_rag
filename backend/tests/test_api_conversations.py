"""
API测试 - conversations endpoints
目标提升API层覆盖率
"""
import pytest
from unittest.mock import Mock, patch

class TestConversationsAPI:
    """测试对话API"""

    @pytest.fixture
    def mock_client(self):
        """Mock FastAPI test client"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        return client

    @pytest.fixture
    def auth_headers(self):
        """测试认证头"""
        return {"Authorization": "Bearer test_token"}

    def test_list_conversations(self, mock_client, auth_headers):
        """测试获取对话列表"""
        # Mock数据库查询
        with patch('app.api.conversations.db_session') as mock_db:
            mock_db.query.return_value.filter.return_value.all.return_value = []
            
            response = mock_client.get("/api/conversations", headers=auth_headers)
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_create_conversation(self, mock_client, auth_headers):
        """测试创建对话"""
        with patch('app.api.conversations.db_session') as mock_db:
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            
            response = mock_client.post(
                "/api/conversations",
                json={"knowledge_base_id": 1, "title": "测试对话"},
                headers=auth_headers
            )
            
            assert response.status_code in [200, 201]
            mock_db.add.assert_called_once()

    def test_get_conversation(self, mock_client, auth_headers):
        """测试获取单个对话"""
        with patch('app.api.conversations.db_session') as mock_db:
            mock_conv = Mock(id=1, title="对话1")
            mock_db.query.return_value.filter.return_value.first.return_value = mock_conv
            
            response = mock_client.get(f"/api/conversations/1", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1

    def test_update_conversation(self, mock_client, auth_headers):
        """测试更新对话"""
        with patch('app.api.conversations.db_session') as mock_db:
            mock_db.commit = Mock()
            
            response = mock_client.put(
                "/api/conversations/1",
                json={"title": "更新标题"},
                headers=auth_headers
            )
            
            assert response.status_code in [200, 204]
            mock_db.commit.assert_called_once()

    def test_delete_conversation(self, mock_client, auth_headers):
        """测试删除对话"""
        with patch('app.api.conversations.db_session') as mock_db:
            mock_db.commit = Mock()
            
            response = mock_client.delete(f"/api/conversations/1", headers=auth_headers)
            
            assert response.status_code == 204
            mock_db.commit.assert_called_once()

    def test_get_conversation_messages(self, mock_client, auth_headers):
        """测试获取对话消息"""
        with patch('app.api.conversations.db_session') as mock_db:
            mock_messages = [Mock(id=i, content=f"message{i}") for i in range(1, 4)]
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_messages
            
            response = mock_client.get(
                "/api/conversations/1/messages",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            messages = response.json()
            assert len(messages) == 3

    def test_conversation_not_found(self, mock_client, auth_headers):
        """测试对话不存在"""
        with patch('app.api.conversations.db_session') as mock_db:
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = mock_client.get(f"/api/conversations/999", headers=auth_headers)
            
            assert response.status_code == 404

    def test_unauthorized_access(self, mock_client):
        """测试未授权访问"""
        response = mock_client.get("/api/conversations")
        
        assert response.status_code == 401

    def test_pagination(self, mock_client, auth_headers):
        """测试分页"""
        with patch('app.api.conversations.db_session') as mock_db:
            mock_db.query.return_value.filter.return_value.all.return_value = [
                Mock(id=i) for i in range(1, 11)
            ]
            
            # 测试页码和页大小
            response = mock_client.get(
                "/api/conversations?page=1&page_size=5",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            conversations = response.json()
            assert len(conversations) == 5
