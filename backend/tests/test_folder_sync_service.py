"""
Folder Sync Service测试 - 目标覆盖 app/services/folder_sync_service.py (173语句)
从16.2%提升至80%+
"""
import pytest
from unittest.mock import Mock, AsyncMock

class TestFolderSyncService:
    """测试文件夹同步服务"""

    @pytest.fixture
    def mock_sync_service(self):
        """Mock同步服务"""
        from app.services.folder_sync_service import FolderSyncService
        
        mock_db = Mock()
        mock_watcher = Mock()
        
        service = FolderSyncService(
            db_session=mock_db,
            file_watcher=mock_watcher
        )
        return service, mock_db, mock_watcher

    def test_create_sync_config(self, mock_sync_service):
        """测试创建同步配置"""
        service, mock_db, _ = mock_sync_service
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        config = service.create_sync_config(
            knowledge_base_id=1,
            folder_path="/path/to/folder",
            sync_interval_seconds=60
        )
        
        assert config.knowledge_base_id == 1
        assert config.folder_path == "/path/to/folder"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_sync_config(self, mock_sync_service):
        """测试获取同步配置"""
        service, mock_db, _ = mock_sync_service
        
        mock_config = Mock(
            id=1,
            knowledge_base_id=1,
            folder_path="/test/path"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        
        result = service.get_sync_config(sync_id=1)
        
        assert result.id == 1
        assert result.folder_path == "/test/path"

    def test_start_sync(self, mock_sync_service):
        """测试启动同步"""
        service, _, mock_watcher = mock_sync_service
        
        mock_config = Mock(id=1, folder_path="/test/path")
        mock_watcher.watch = Mock(return_value=True)
        
        result = service.start_sync(config=mock_config)
        
        assert result is True
        mock_watcher.watch.assert_called_once_with("/test/path")

    def test_stop_sync(self, mock_sync_service):
        """测试停止同步"""
        service, _, mock_watcher = mock_sync_service
        
        mock_watcher.unwatch = Mock(return_value=True)
        
        result = service.stop_sync(watch_id="watch123")
        
        assert result is True
        mock_watcher.unwatch.assert_called_once_with("watch123")

    def test_get_sync_status(self, mock_sync_service):
        """测试获取同步状态"""
        service, mock_db, _ = mock_sync_service
        
        mock_log = Mock(
            id=1,
            sync_id=1,
            status="running",
            synced_count=5,
            error_count=0
        )
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_log
        
        result = service.get_sync_status(sync_id=1)
        
        assert result.status == "running"
        assert result.synced_count == 5
