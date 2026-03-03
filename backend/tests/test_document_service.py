"""
Document Service测试 - 目标覆盖 app/services/document_service.py (265语句)
从16.2%提升至80%+
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

class TestDocumentService:
    """测试文档服务"""

    @pytest.fixture
    def mock_doc_service(self):
        """Mock文档服务"""
        from app.services.document_service import DocumentService
        
        mock_db = Mock()
        mock_parser = Mock()
        
        service = DocumentService(
            db_session=mock_db,
            parser=mock_parser
        )
        return service, mock_db, mock_parser

    def test_upload_document_success(self, mock_doc_service):
        """测试文档上传成功"""
        service, mock_db, _ = mock_doc_service
        
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        
        # Mock解析器返回分块
        mock_parser.parse = Mock(return_value=[
            Mock(id=1, content="chunk1"),
            Mock(id=2, content="chunk2")
        ])
        
        # Mock数据库保存
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        result = service.upload_document(
            file=mock_file,
            knowledge_base_id=1,
            user_id="user123"
        )
        
        assert result is not None
        mock_parser.parse.assert_called_once()
        mock_db.add.assert_called()

    def test_upload_document_invalid_format(self, mock_doc_service):
        """测试无效格式处理"""
        service, _, _ = mock_doc_service
        
        mock_file = Mock()
        mock_file.filename = "test.unknown"
        mock_file.content_type = "application/unknown"
        
        with pytest.raises(ValueError, match="不支持的文件格式"):
            service.upload_document(
                file=mock_file,
                knowledge_base_id=1,
                user_id="user123"
            )

    def test_delete_document(self, mock_doc_service):
        """测试文档删除"""
        service, mock_db, _ = mock_doc_service
        
        # Mock数据库查询和删除
        mock_doc = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        mock_db.delete = Mock()
        
        result = service.delete_document(document_id=1)
        
        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_document_by_id(self, mock_doc_service):
        """测试通过ID获取文档"""
        service, mock_db, _ = mock_doc_service
        
        mock_doc = Mock(id=1, filename="test.pdf")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        
        result = service.get_document_by_id(1)
        
        assert result.id == 1
        assert result.filename == "test.pdf"

    def test_list_documents_by_kb(self, mock_doc_service):
        """测试列出知识库文档"""
        service, mock_db, _ = mock_doc_service
        
        mock_docs = [Mock(id=i, filename=f"doc{i}.pdf") for i in range(1, 4)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_docs
        
        result = service.list_documents(knowledge_base_id=1)
        
        assert len(result) == 3
        assert result[0].id == 1

    def test_update_document_metadata(self, mock_doc_service):
        """测试更新文档元数据"""
        service, mock_db, _ = mock_doc_service
        
        mock_doc = Mock(id=1, metadata={"old": "data"})
        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        mock_db.commit = Mock()
        
        service.update_document_metadata(
            document_id=1,
            metadata={"new": "data"}
        )
        
        assert mock_doc.metadata == {"new": "data"}
        mock_db.commit.assert_called_once()
