"""
Document version management tests.

Tests for C2-3.1.1: 文档版本管理功能
- 版本历史查询
- 版本切换
- 向量库同步

Author: C2
Date: 2026-02-13
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.models import Document
from app.services.document_service import DocumentService


class TestDocumentVersionService:
    """Test DocumentService version management methods."""

    def test_list_versions_document_not_found(self):
        """Test list_versions returns error when document not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with patch.object(DocumentService, 'get_by_id', return_value=None):
            versions, err = DocumentService.list_versions(mock_db, 9999)

        assert versions == []
        assert err == "文档不存在"

    def test_list_versions_success(self):
        """Test list_versions returns all versions of a document."""
        mock_db = MagicMock(spec=Session)
        
        # Mock document
        mock_doc = MagicMock(spec=Document)
        mock_doc.knowledge_base_id = 1
        mock_doc.filename = "test.pdf"
        
        # Mock versions
        mock_v1 = MagicMock(spec=Document)
        mock_v1.id = 1
        mock_v1.version = 1
        mock_v1.is_current = False
        
        mock_v2 = MagicMock(spec=Document)
        mock_v2.id = 2
        mock_v2.version = 2
        mock_v2.is_current = True
        
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_v2, mock_v1]
        
        with patch.object(DocumentService, 'get_by_id', return_value=mock_doc):
            versions, err = DocumentService.list_versions(mock_db, 1)

        assert err is None
        assert len(versions) == 2
        assert versions[0].version == 2  # Latest first
        assert versions[1].version == 1

    def test_activate_version_document_not_found(self):
        """Test activate_version returns error when document not found."""
        mock_db = MagicMock(spec=Session)
        
        with patch.object(DocumentService, 'get_by_id', return_value=None):
            doc, err = DocumentService.activate_version(mock_db, 9999)

        assert doc is None
        assert err == "文档不存在"

    def test_activate_version_already_current(self):
        """Test activate_version returns immediately if already current."""
        mock_db = MagicMock(spec=Session)
        
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1
        mock_doc.is_current = True
        
        with patch.object(DocumentService, 'get_by_id', return_value=mock_doc):
            doc, err = DocumentService.activate_version(mock_db, 1)

        assert doc == mock_doc
        assert err is None
        # Should not call commit since no changes
        mock_db.commit.assert_not_called()

    def test_activate_version_switches_and_syncs_vectors(self):
        """Test activate_version switches version and syncs vector store."""
        mock_db = MagicMock(spec=Session)
        
        # Target document (not current)
        mock_target = MagicMock(spec=Document)
        mock_target.id = 2
        mock_target.knowledge_base_id = 1
        mock_target.filename = "test.pdf"
        mock_target.is_current = False
        mock_target.content_text = "Test content for vectorization"
        mock_target.status = "parsed"
        
        # Current document
        mock_current = MagicMock(spec=Document)
        mock_current.id = 1
        mock_current.knowledge_base_id = 1
        mock_current.is_current = True
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_current
        
        # Mock vector store
        mock_vector_store = MagicMock()
        mock_vector_store.delete_document_chunks.return_value = (True, None)
        mock_vector_store.upsert_document_chunks.return_value = (True, None)
        
        # Mock chunker and embedding
        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = ["chunk1", "chunk2"]
        
        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        
        with patch.object(DocumentService, 'get_by_id', return_value=mock_target), \
             patch.object(DocumentService, '_vector_store', mock_vector_store), \
             patch.object(DocumentService, '_chunker', mock_chunker), \
             patch.object(DocumentService, '_embedding_service', mock_embedding):
            
            doc, err = DocumentService.activate_version(mock_db, 2)

        assert err is None
        # Verify old version's vectors were deleted
        mock_vector_store.delete_document_chunks.assert_called_once_with(
            knowledge_base_id=1,
            document_id=1,
        )
        # Verify new version's vectors were created
        mock_vector_store.upsert_document_chunks.assert_called_once()
        # Verify is_current flags were updated
        assert mock_current.is_current == False
        assert mock_target.is_current == True
        # Verify commit was called
        mock_db.commit.assert_called()


class TestDocumentVersionAPI:
    """Test document version API endpoints."""

    def test_list_versions_api(self, client, auth_headers):
        """Test GET /documents/{id}/versions endpoint."""
        # This test requires a real document in DB
        # For unit test, we mock the service
        with patch.object(DocumentService, 'list_versions') as mock_list:
            mock_doc = MagicMock()
            mock_doc.id = 1
            mock_doc.knowledge_base_id = 1
            mock_doc.title = "Test"
            mock_doc.filename = "test.pdf"
            mock_doc.file_type = "pdf"
            mock_doc.file_size = 1024
            mock_doc.file_hash = "abc123"
            mock_doc.status = "vectorized"
            mock_doc.parser_message = "OK"
            mock_doc.version = 1
            mock_doc.parent_document_id = None
            mock_doc.is_current = True
            mock_doc.created_by = 1
            mock_doc.created_at = "2026-02-13T10:00:00"
            mock_doc.updated_at = "2026-02-13T10:00:00"
            mock_doc.source_url = None
            
            mock_list.return_value = ([mock_doc], None)
            
            resp = client.get("/api/documents/1/versions", headers=auth_headers)
            
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1

    def test_list_versions_api_not_found(self, client, auth_headers):
        """Test GET /documents/{id}/versions returns error for non-existent doc."""
        with patch.object(DocumentService, 'list_versions') as mock_list:
            mock_list.return_value = ([], "文档不存在")
            
            resp = client.get("/api/documents/9999/versions", headers=auth_headers)
            
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 4040
        assert "不存在" in data["detail"]

    def test_activate_version_api(self, client, auth_headers):
        """Test POST /documents/{id}/activate endpoint."""
        with patch.object(DocumentService, 'activate_version') as mock_activate:
            mock_doc = MagicMock()
            mock_doc.id = 2
            mock_doc.knowledge_base_id = 1
            mock_doc.title = "Test"
            mock_doc.filename = "test.pdf"
            mock_doc.file_type = "pdf"
            mock_doc.file_size = 1024
            mock_doc.file_hash = "abc123"
            mock_doc.status = "vectorized"
            mock_doc.parser_message = "版本切换，分块 2，向量化完成"
            mock_doc.version = 2
            mock_doc.parent_document_id = 1
            mock_doc.is_current = True
            mock_doc.created_by = 1
            mock_doc.created_at = "2026-02-13T10:00:00"
            mock_doc.updated_at = "2026-02-13T10:00:00"
            mock_doc.source_url = None
            
            mock_activate.return_value = (mock_doc, None)
            
            resp = client.post("/api/documents/2/activate", headers=auth_headers)
            
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["is_current"] == True

    def test_activate_version_api_error(self, client, auth_headers):
        """Test POST /documents/{id}/activate returns error on failure."""
        with patch.object(DocumentService, 'activate_version') as mock_activate:
            mock_activate.return_value = (None, "文档不存在")
            
            resp = client.post("/api/documents/9999/activate", headers=auth_headers)
            
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 4001
        assert "不存在" in data["detail"]


class TestVectorStoreDeleteChunks:
    """Test ChromaVectorStore delete_document_chunks method."""

    def test_delete_document_chunks_success(self):
        """Test delete_document_chunks successfully deletes vectors."""
        from app.rag.vector_store import ChromaVectorStore
        
        store = ChromaVectorStore(host="localhost", port=8000, collection_prefix="test")
        
        with patch('httpx.get') as mock_get, \
             patch('httpx.post') as mock_post:
            
            # Mock collection exists
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"id": "col-123"}
            
            # Mock delete success
            mock_post.return_value.status_code = 200
            
            ok, err = store.delete_document_chunks(knowledge_base_id=1, document_id=1)
            
        assert ok is True
        assert err is None

    def test_delete_document_chunks_failure(self):
        """Test delete_document_chunks handles errors."""
        from app.rag.vector_store import ChromaVectorStore
        
        store = ChromaVectorStore(host="localhost", port=8000, collection_prefix="test")
        
        with patch('httpx.get') as mock_get, \
             patch('httpx.post') as mock_post:
            
            # Mock collection exists
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"id": "col-123"}
            
            # Mock delete failure
            mock_post.return_value.status_code = 500
            mock_post.return_value.text = "Internal Server Error"
            
            ok, err = store.delete_document_chunks(knowledge_base_id=1, document_id=1)
            
        assert ok is False
        assert "删除向量失败" in err
