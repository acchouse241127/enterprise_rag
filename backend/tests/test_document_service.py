"""
Unit tests for Document_service.py.

Tests for app/services/document_service.py
Author: C2
"""

import hashlib
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from io import BytesIO
from fastapi import UploadFile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.document_parser import get_parser_for_extension
from app.models import Document, KnowledgeBase


from app.rag import BgeM3EmbeddingService, ChromaVectorStore, TextChunker


from app.rag.chunker import ChunkMode


class TestDocumentServiceListByKb:
    """Tests for list_by_kb method."""

    def test_list_by_kb_returns_documents(self):
        """Test list_by_kb returns documents."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_docs = [MagicMock(id=1), MagicMock(id=2)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_docs
        mock_db.execute.return_value = mock_result

        result = DocumentService.list_by_kb(mock_db, 1)
        assert result == mock_docs


class TestDocumentServiceGetById:
    """Tests for get_by_id method."""

    def test_get_by_id_found(self):
        """Test get_by_id returns document."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        mock_db.execute.return_value = mock_result

        result = DocumentService.get_by_id(mock_db, 1)
        assert result == mock_doc

    def test_get_by_id_not_found(self):
        """Test get_by_id returns None when not found."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = DocumentService.get_by_id(mock_db, 999)
        assert result is None


class TestDocumentServiceCreateDocument:
    """Tests for _create_document method."""

    def test_create_document_success(self):
        """Test _create_document creates a document."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1

        with patch("app.services.document_service.Document") as MockDoc:
            MockDoc.return_value = mock_doc

            result = DocumentService._create_document(
                mock_db,
                knowledge_base_id=1,
                filename="test.txt",
                file_type="txt",
                file_path="/path/to/test.txt",
                file_hash="abc123",
            )
            assert result == mock_doc
            mock_db.add.assert_called()
            mock_db.commit.assert_called()


class TestDocumentServiceChunkText:
    """Tests for _chunk_text method."""

    def test_chunk_text_empty(self):
        """Test _chunk_text with empty text."""
        from app.services.document_service import DocumentService

        result = DocumentService._chunk_text("", "test.txt", "txt", 500, 50)
        assert result == []

    def test_chunk_text_basic(self):
        """Test _chunk_text with basic text."""
        from app.services.document_service import DocumentService

        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = ["chunk1", "chunk2"]

        with patch("app.services.document_service.TextChunker") as MockChunker:
            MockChunker.return_value = mock_chunker

            result = DocumentService._chunk_text(
                "test content", "test.txt", "txt", 500, 50
            )
            assert len(result) == 2


class TestDocumentServiceGetVersion:
    """Tests for get_version method."""

    def test_get_version_found(self):
        """Test get_version returns version."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.version = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        mock_db.execute.return_value = mock_result

        result, err = DocumentService.get_version(mock_db, 1)
        assert result == 1
        assert err is None

    def test_get_version_not_found(self):
        """Test get_version returns None when not found."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result, err = DocumentService.get_version(mock_db, 999)
        assert result is None
        assert err == "文档不存在"


class TestDocumentServiceUpdateStatus:
    """Tests for update_status method."""

    def test_update_status_success(self):
        """Test update_status updates status."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1

        with patch.object(DocumentService, "get_by_id", return_value=mock_doc):
            result, err = DocumentService.update_status(mock_db, 1, "parsed", "解析成功")
            assert result == mock_doc
            assert err is None
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    def test_update_status_not_found(self):
        """Test update_status returns error when document not found."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()

        with patch.object(DocumentService, "get_by_id", return_value=None):
            result, err = DocumentService.update_status(mock_db, 999, "parsed", "test")
            assert result is None
            assert err == "文档不存在"


class TestDocumentServiceCalculateHash:
    """Tests for _calculate_hash method."""

    def test_calculate_hash_basic(self):
        """Test _calculate_hash returns correct hash."""
        from app.services.document_service import DocumentService

        content = b"test content"
        result = DocumentService._calculate_hash(content)
        assert result == hashlib.sha256(content).hexdigest()

    def test_calculate_hash_empty(self):
        """Test _calculate_hash with empty content."""
        from app.services.document_service import DocumentService

        result = DocumentService._calculate_hash(b"")
        assert result == hashlib.sha256(b"").hexdigest()
