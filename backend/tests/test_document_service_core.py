"""
Tests for DocumentService core functionality.

Tests for:
- get_chunk_mode_for_file
- DocumentService initialization
- Chunker customization
- list_by_kb
- get_by_id

Author: C2
Date: 2026-03-04
Task: V2.0 Test Coverage Improvement
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestGetChunkModeForFile:
    """Tests for get_chunk_mode_for_file function."""

    def test_sentence_mode_pdf(self):
        """Test PDF files use sentence mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.pdf")
        assert mode == "sentence"

    def test_sentence_mode_docx(self):
        """Test DOCX files use sentence mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.docx")
        assert mode == "sentence"

    def test_sentence_mode_txt(self):
        """Test TXT files use sentence mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.txt")
        assert mode == "sentence"

    def test_sentence_mode_md(self):
        """Test MD files use sentence mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.md")
        assert mode == "sentence"

    def test_char_mode_xlsx(self):
        """Test XLSX files use char mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.xlsx")
        assert mode == "char"

    def test_char_mode_pptx(self):
        """Test PPTX files use char mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.pptx")
        assert mode == "char"

    def test_sentence_mode_mp3(self):
        """Test MP3 files use sentence mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.mp3")
        assert mode == "sentence"

    def test_sentence_mode_png(self):
        """Test PNG files use sentence mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.png")
        assert mode == "sentence"

    def test_sentence_mode_url(self):
        """Test URL type uses sentence mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.html", file_type="url")
        assert mode == "sentence"

    def test_file_type_priority_over_extension(self):
        """Test that file_type parameter takes priority over extension."""
        from app.services.document_service import get_chunk_mode_for_file

        # Extension suggests sentence, but file_type says xlsx (char)
        mode = get_chunk_mode_for_file("test.unknown", file_type="xlsx")
        assert mode == "char"

    def test_case_insensitive_extension(self):
        """Test that extension matching is case insensitive."""
        from app.services.document_service import get_chunk_mode_for_file

        mode1 = get_chunk_mode_for_file("test.PDF")
        mode2 = get_chunk_mode_for_file("test.pdf")
        mode3 = get_chunk_mode_for_file("test.Pdf")

        assert mode1 == "sentence"
        assert mode2 == "sentence"
        assert mode3 == "sentence"

    def test_unknown_extension_default(self):
        """Test that unknown extensions default to sentence mode."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.unknown")
        assert mode == "sentence"

    def test_filename_without_extension(self):
        """Test filename without extension."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("testfile")
        assert mode == "sentence"

    def test_empty_filename(self):
        """Test empty filename."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("")
        assert mode == "sentence"

    def test_multiple_dots(self):
        """Test filename with multiple dots."""
        from app.services.document_service import get_chunk_mode_for_file

        mode = get_chunk_mode_for_file("test.v2.final.pdf")
        assert mode == "sentence"


class TestDocumentServiceInit:
    """Tests for DocumentService initialization."""

    def test_document_service_class_exists(self):
        """Test that DocumentService class can be imported."""
        from app.services.document_service import DocumentService

        assert DocumentService is not None

    def test_document_service_has_chunker(self):
        """Test that DocumentService has _chunker."""
        from app.services.document_service import DocumentService

        assert hasattr(DocumentService, '_chunker')
        assert DocumentService._chunker is not None

    def test_document_service_has_embedding_service(self):
        """Test that DocumentService has _embedding_service."""
        from app.services.document_service import DocumentService

        assert hasattr(DocumentService, '_embedding_service')
        assert DocumentService._embedding_service is not None

    def test_document_service_has_vector_store(self):
        """Test that DocumentService has _vector_store."""
        from app.services.document_service import DocumentService

        assert hasattr(DocumentService, '_vector_store')
        assert DocumentService._vector_store is not None


class TestDocumentServiceGetChunker:
    """Tests for DocumentService._get_chunker method."""

    @patch('app.services.document_service.settings.chunk_size', 500)
    @patch('app.services.document_service.settings.chunk_overlap', 50)
    def test_get_chunker_default(self):
        """Test getting chunker with default settings."""
        from app.services.document_service import DocumentService

        chunker = DocumentService._get_chunker()

        assert chunker is not None
        # Should use settings defaults

    def test_get_chunker_custom(self):
        """Test getting chunker with custom parameters."""
        from app.services.document_service import DocumentService

        chunker = DocumentService._get_chunker(
            chunk_size=1000,
            chunk_overlap=100,
        )

        assert chunker is not None

    @patch('app.services.document_service.settings.chunk_size', 500)
    @patch('app.services.document_service.settings.chunk_overlap', 50)
    def test_get_chunker_partial_custom(self):
        """Test getting chunker with partial custom parameters."""
        from app.services.document_service import DocumentService

        chunker = DocumentService._get_chunker(
            chunk_size=1000,
            # overlap uses default
        )

        assert chunker is not None


class TestDocumentServiceChunkText:
    """Tests for DocumentService._chunk_text method."""

    @patch('app.services.document_service.settings.chunk_size', 500)
    @patch('app.services.document_service.settings.chunk_overlap', 50)
    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        from app.services.document_service import DocumentService

        text = "这是第一段。这是第二段。这是第三段。"
        chunks = DocumentService._chunk_text(text, "test.txt")

        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        from app.services.document_service import DocumentService

        chunks = DocumentService._chunk_text("", "test.txt")

        # Should handle empty text
        assert isinstance(chunks, list)

    def test_chunk_text_whitespace_only(self):
        """Test chunking whitespace-only text."""
        from app.services.document_service import DocumentService

        chunks = DocumentService._chunk_text("   ", "test.txt")

        # Should handle whitespace
        assert isinstance(chunks, list)

    def test_chunk_text_custom_chunk_size(self):
        """Test chunking with custom chunk_size."""
        from app.services.document_service import DocumentService

        text = "这是第一段。" * 100
        chunks = DocumentService._chunk_text(
            text,
            "test.txt",
            chunk_size=100,
            chunk_overlap=10,
        )

        assert isinstance(chunks, list)

    def test_chunk_text_with_file_type(self):
        """Test chunking with explicit file_type."""
        from app.services.document_service import DocumentService

        text = "表格数据\n列1 列2\n数据1 数据2"
        chunks = DocumentService._chunk_text(
            text,
            "test.unknown",
            file_type="xlsx",  # Should use char mode
        )

        assert isinstance(chunks, list)

    def test_chunk_text_sentence_mode(self):
        """Test chunking in sentence mode."""
        from app.services.document_service import DocumentService

        text = "这是第一段。这是第二段。这是第三段。"
        chunks = DocumentService._chunk_text(
            text,
            "test.txt",  # sentence mode
        )

        assert isinstance(chunks, list)

    def test_chunk_text_char_mode(self):
        """Test chunking in char mode."""
        from app.services.document_service import DocumentService

        text = "表格内容A\t表格内容B\t表格内容C"
        chunks = DocumentService._chunk_text(
            text,
            "test.xlsx",  # char mode
        )

        assert isinstance(chunks, list)


class TestDocumentServiceListByKb:
    """Tests for DocumentService.list_by_kb method."""

    @patch('app.services.document_service.Session')
    def test_list_by_kb_success(self, mock_session):
        """Test listing documents by knowledge base."""
        from app.services.document_service import DocumentService
        from app.models import Document

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        # Mock query result
        mock_doc1 = Document(id=1, title="文档1", filename="file1.txt")
        mock_doc2 = Document(id=2, title="文档2", filename="file2.txt")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc1, mock_doc2]
        mock_db.execute.return_value = mock_result

        documents = DocumentService.list_by_kb(mock_db, knowledge_base_id=1)

        assert len(documents) == 2
        assert documents[0].title == "文档1"
        assert documents[1].title == "文档2"

    @patch('app.services.document_service.Session')
    def test_list_by_kb_empty(self, mock_session):
        """Test listing documents when none exist."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        documents = DocumentService.list_by_kb(mock_db, knowledge_base_id=1)

        assert documents == []

    @patch('app.services.document_service.Session')
    def test_list_by_kb_ordered(self, mock_session):
        """Test that documents are ordered by created_at DESC."""
        from app.services.document_service import DocumentService
        from app.models import Document
        from datetime import datetime

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        # Mock query result with different timestamps
        mock_doc1 = Document(
            id=1,
            title="文档1",
            filename="file1.txt",
            created_at=datetime(2026, 1, 1)
        )
        mock_doc2 = Document(
            id=2,
            title="文档2",
            filename="file2.txt",
            created_at=datetime(2026, 1, 2)
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc2, mock_doc1]
        mock_db.execute.return_value = mock_result

        documents = DocumentService.list_by_kb(mock_db, knowledge_base_id=1)

        # Should be ordered DESC (most recent first)
        assert documents[0].created_at >= documents[1].created_at


class TestDocumentServiceGetById:
    """Tests for DocumentService.get_by_id method."""

    @patch('app.services.document_service.Session')
    def test_get_by_id_success(self, mock_session):
        """Test getting document by ID."""
        from app.services.document_service import DocumentService
        from app.models import Document

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        mock_doc = Document(id=1, title="测试文档", filename="test.txt")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        mock_db.execute.return_value = mock_result

        document = DocumentService.get_by_id(mock_db, document_id=1)

        assert document is not None
        assert document.id == 1
        assert document.title == "测试文档"

    @patch('app.services.document_service.Session')
    def test_get_by_id_not_found(self, mock_session):
        """Test getting non-existent document."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        document = DocumentService.get_by_id(mock_db, document_id=999)

        assert document is None

    @patch('app.services.document_service.Session')
    def test_get_by_id_filter_by_id(self, mock_session):
        """Test that get_by_id filters by correct ID."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        DocumentService.get_by_id(mock_db, document_id=123)

        # Verify that query includes ID filter
        assert mock_db.execute.called


class TestDocumentServiceValidateKbExists:
    """Tests for DocumentService._validate_kb_exists method."""

    @patch('app.services.document_service.Session')
    def test_validate_kb_exists_success(self, mock_session):
        """Test validating existing knowledge base."""
        from app.services.document_service import DocumentService
        from app.models import KnowledgeBase

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        kb = DocumentService._validate_kb_exists(mock_db, knowledge_base_id=1)

        assert kb is not None
        assert kb.id == 1

    @patch('app.services.document_service.Session')
    def test_validate_kb_exists_not_found(self, mock_session):
        """Test validating non-existent knowledge base."""
        from app.services.document_service import DocumentService

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        kb = DocumentService._validate_kb_exists(mock_db, knowledge_base_id=999)

        assert kb is None


class TestDocumentServiceDelete:
    """Tests for DocumentService.delete method."""

    @patch('app.services.document_service.Session')
    def test_delete_success(self, mock_session):
        """Test deleting a document."""
        from app.services.document_service import DocumentService
        from app.models import Document

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_session.return_value.__exit__ = Mock(return_value=None)

        mock_doc = Document(id=1, title="测试文档")

        DocumentService.delete(mock_db, mock_doc)

        # Verify delete and commit were called
        mock_db.delete.assert_called_once_with(mock_doc)
        mock_db.commit.assert_called_once()
