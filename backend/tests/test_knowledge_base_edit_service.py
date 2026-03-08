"""
Unit tests for KnowledgeBaseEditService.

Tests for app/services/knowledge_base_edit_service.py
Author: C2
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock


class TestGetDocumentContent:
    """Tests for get_document_content method."""

    def test_get_document_content_found(self):
        """Test getting document content successfully."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1
        mock_doc.content_text = "Test content"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        mock_db.execute.return_value = mock_result

        doc, err = KnowledgeBaseEditService.get_document_content(mock_db, 1)
        assert doc == mock_doc
        assert err is None

    def test_get_document_content_not_found(self):
        """Test getting document content when not found."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        doc, err = KnowledgeBaseEditService.get_document_content(mock_db, 999)
        assert doc is None
        assert err == "文档不存在"


class TestUpdateDocumentContent:
    """Tests for update_document_content method."""

    def test_update_document_content_not_found(self):
        """Test update when document not found."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        doc, err = KnowledgeBaseEditService.update_document_content(
            mock_db, 999, "new content"
        )
        assert doc is None
        assert err == "文档不存在"

    def test_update_document_content_empty(self):
        """Test update with empty content."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        mock_db.execute.return_value = mock_result

        doc, err = KnowledgeBaseEditService.update_document_content(
            mock_db, 1, "   "
        )
        assert doc is None
        assert err == "内容不能为空"

    def test_update_document_content_success(self):
        """Test successful content update."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1
        mock_doc.knowledge_base_id = 1
        mock_doc.content_text = "old content"

        mock_kb = MagicMock()
        mock_kb.chunk_size = 500
        mock_kb.chunk_overlap = 50

        def execute_side_effect(stmt):
            mock_result = MagicMock()
            # First call returns doc, second returns kb
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1
            if execute_side_effect.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_doc
            else:
                mock_result.scalar_one_or_none.return_value = mock_kb
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        with patch.object(KnowledgeBaseEditService, '_vector_store') as mock_vs:
            with patch.object(KnowledgeBaseEditService, '_embedding_service') as mock_emb:
                with patch('app.services.knowledge_base_edit_service.TextChunker') as MockChunker:
                    mock_chunker = MagicMock()
                    mock_chunker.chunk_text.return_value = ["chunk1", "chunk2"]
                    MockChunker.return_value = mock_chunker
                    mock_emb.embed_texts.return_value = [[0.1, 0.2], [0.3, 0.4]]

                    doc, err = KnowledgeBaseEditService.update_document_content(
                        mock_db, 1, "new content"
                    )
                    assert err is None
                    mock_db.commit.assert_called()
                    mock_vs.delete_document_chunks.assert_called()

    def test_update_document_content_exception(self):
        """Test update with exception."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1
        mock_doc.knowledge_base_id = 1

        mock_kb = MagicMock()
        mock_kb.chunk_size = 500
        mock_kb.chunk_overlap = 50

        def execute_side_effect(stmt):
            mock_result = MagicMock()
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1
            if execute_side_effect.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_doc
            else:
                mock_result.scalar_one_or_none.return_value = mock_kb
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        with patch.object(KnowledgeBaseEditService, '_vector_store') as mock_vs:
            with patch('app.services.knowledge_base_edit_service.TextChunker') as MockChunker:
                # Set up chunker that works
                mock_chunker = MagicMock()
                mock_chunker.chunk_text.return_value = ["chunk1"]
                MockChunker.return_value = mock_chunker

                # But vector store fails
                mock_vs.delete_document_chunks.side_effect = Exception("Vector store error")

                doc, err = KnowledgeBaseEditService.update_document_content(
                    mock_db, 1, "new content"
                )
                assert doc is None
                assert "更新失败" in err
                mock_db.rollback.assert_called()


class TestGetKbChunkSettings:
    """Tests for get_kb_chunk_settings method."""

    def test_get_kb_chunk_settings_found(self):
        """Test getting KB chunk settings successfully."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_kb.id = 1
        mock_kb.chunk_size = 500
        mock_kb.chunk_overlap = 50

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        with patch('app.services.knowledge_base_edit_service.settings') as mock_settings:
            mock_settings.chunk_size = 1000
            mock_settings.chunk_overlap = 100

            result = KnowledgeBaseEditService.get_kb_chunk_settings(mock_db, 1)
            assert result is not None
            assert result["chunk_size"] == 500
            assert result["chunk_overlap"] == 50
            assert result["is_custom"] is True

    def test_get_kb_chunk_settings_not_found(self):
        """Test getting KB chunk settings when KB not found."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = KnowledgeBaseEditService.get_kb_chunk_settings(mock_db, 999)
        assert result is None

    def test_get_kb_chunk_settings_defaults(self):
        """Test getting KB chunk settings with defaults."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_kb.id = 1
        mock_kb.chunk_size = None
        mock_kb.chunk_overlap = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        with patch('app.services.knowledge_base_edit_service.settings') as mock_settings:
            mock_settings.chunk_size = 1000
            mock_settings.chunk_overlap = 100

            result = KnowledgeBaseEditService.get_kb_chunk_settings(mock_db, 1)
            assert result["chunk_size"] == 1000
            assert result["chunk_overlap"] == 100
            assert result["is_custom"] is False


class TestUpdateKbChunkSettings:
    """Tests for update_kb_chunk_settings method."""

    def test_update_kb_chunk_settings_not_found(self):
        """Test update when KB not found."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        kb, err = KnowledgeBaseEditService.update_kb_chunk_settings(
            mock_db, 999, chunk_size=500
        )
        assert kb is None
        assert err == "知识库不存在"

    def test_update_kb_chunk_settings_invalid_size_low(self):
        """Test update with invalid chunk_size (too low)."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        kb, err = KnowledgeBaseEditService.update_kb_chunk_settings(
            mock_db, 1, chunk_size=50
        )
        assert kb is None
        assert "chunk_size 必须在 100-10000 之间" in err

    def test_update_kb_chunk_settings_invalid_size_high(self):
        """Test update with invalid chunk_size (too high)."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        kb, err = KnowledgeBaseEditService.update_kb_chunk_settings(
            mock_db, 1, chunk_size=20000
        )
        assert kb is None
        assert "chunk_size 必须在 100-10000 之间" in err

    def test_update_kb_chunk_settings_invalid_overlap_low(self):
        """Test update with invalid chunk_overlap (too low)."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        kb, err = KnowledgeBaseEditService.update_kb_chunk_settings(
            mock_db, 1, chunk_overlap=-10
        )
        assert kb is None
        assert "chunk_overlap 必须在 0-500 之间" in err

    def test_update_kb_chunk_settings_invalid_overlap_high(self):
        """Test update with invalid chunk_overlap (too high)."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        kb, err = KnowledgeBaseEditService.update_kb_chunk_settings(
            mock_db, 1, chunk_overlap=600
        )
        assert kb is None
        assert "chunk_overlap 必须在 0-500 之间" in err

    def test_update_kb_chunk_settings_overlap_greater_than_size(self):
        """Test update with overlap >= size."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        kb, err = KnowledgeBaseEditService.update_kb_chunk_settings(
            mock_db, 1, chunk_size=200, chunk_overlap=200
        )
        assert kb is None
        assert "chunk_overlap 必须小于 chunk_size" in err

    def test_update_kb_chunk_settings_success(self):
        """Test successful settings update."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_kb.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_kb
        mock_db.execute.return_value = mock_result

        kb, err = KnowledgeBaseEditService.update_kb_chunk_settings(
            mock_db, 1, chunk_size=500, chunk_overlap=50
        )
        assert kb == mock_kb
        assert err is None
        assert mock_kb.chunk_size == 500
        assert mock_kb.chunk_overlap == 50
        mock_db.commit.assert_called()


class TestRechunkDocument:
    """Tests for rechunk_document method."""

    def test_rechunk_document_not_found(self):
        """Test rechunk when document not found."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        doc, count, err = KnowledgeBaseEditService.rechunk_document(mock_db, 999)
        assert doc is None
        assert count == 0
        assert err == "文档不存在"

    def test_rechunk_document_empty_content(self):
        """Test rechunk when document has no content."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.content_text = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        mock_db.execute.return_value = mock_result

        doc, count, err = KnowledgeBaseEditService.rechunk_document(mock_db, 1)
        assert doc is None
        assert count == 0
        assert err == "文档内容为空，无法分块"

    def test_rechunk_document_invalid_params(self):
        """Test rechunk with invalid parameters."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.content_text = "Some content"
        mock_doc.knowledge_base_id = 1

        mock_kb = MagicMock()
        mock_kb.chunk_size = None
        mock_kb.chunk_overlap = None

        def execute_side_effect(stmt):
            mock_result = MagicMock()
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1
            if execute_side_effect.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_doc
            else:
                mock_result.scalar_one_or_none.return_value = mock_kb
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        with patch('app.services.knowledge_base_edit_service.settings') as mock_settings:
            mock_settings.chunk_size = 100
            mock_settings.chunk_overlap = 150  # overlap >= size

            doc, count, err = KnowledgeBaseEditService.rechunk_document(
                mock_db, 1, chunk_size=100, chunk_overlap=100
            )
            assert doc is None
            assert count == 0
            assert "chunk_overlap 必须小于 chunk_size" in err

    def test_rechunk_document_success(self):
        """Test successful document rechunking."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1
        mock_doc.content_text = "Some content to chunk"
        mock_doc.knowledge_base_id = 1

        mock_kb = MagicMock()
        mock_kb.chunk_size = 500
        mock_kb.chunk_overlap = 50

        def execute_side_effect(stmt):
            mock_result = MagicMock()
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1
            if execute_side_effect.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_doc
            else:
                mock_result.scalar_one_or_none.return_value = mock_kb
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        with patch.object(KnowledgeBaseEditService, '_vector_store') as mock_vs:
            with patch.object(KnowledgeBaseEditService, '_embedding_service') as mock_emb:
                with patch('app.services.knowledge_base_edit_service.TextChunker') as MockChunker:
                    mock_chunker = MagicMock()
                    mock_chunker.chunk_text.return_value = ["chunk1", "chunk2", "chunk3"]
                    MockChunker.return_value = mock_chunker
                    mock_emb.embed_texts.return_value = [[0.1] * 10] * 3

                    doc, count, err = KnowledgeBaseEditService.rechunk_document(
                        mock_db, 1, chunk_size=500, chunk_overlap=50
                    )
                    assert err is None
                    assert count == 3
                    mock_db.commit.assert_called()

    def test_rechunk_document_exception(self):
        """Test rechunk with exception."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1
        mock_doc.content_text = "Some content"
        mock_doc.knowledge_base_id = 1

        mock_kb = MagicMock()
        mock_kb.chunk_size = 500
        mock_kb.chunk_overlap = 50

        def execute_side_effect(stmt):
            mock_result = MagicMock()
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1
            if execute_side_effect.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_doc
            else:
                mock_result.scalar_one_or_none.return_value = mock_kb
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        with patch.object(KnowledgeBaseEditService, '_vector_store') as mock_vs:
            with patch('app.services.knowledge_base_edit_service.TextChunker') as MockChunker:
                # Set up chunker that works
                mock_chunker = MagicMock()
                mock_chunker.chunk_text.return_value = ["chunk1"]
                MockChunker.return_value = mock_chunker

                # But vector store fails
                mock_vs.delete_document_chunks.side_effect = Exception("Vector store error")

                doc, count, err = KnowledgeBaseEditService.rechunk_document(mock_db, 1)
                assert doc is None
                assert count == 0
                assert "重新分块失败" in err
                mock_db.rollback.assert_called()


class TestRechunkAllDocuments:
    """Tests for rechunk_all_documents method."""

    def test_rechunk_all_documents_kb_not_found(self):
        """Test rechunk all when KB not found."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        success, failed, err = KnowledgeBaseEditService.rechunk_all_documents(mock_db, 999)
        assert success == 0
        assert failed == 0
        assert err == "知识库不存在"

    def test_rechunk_all_documents_success(self):
        """Test successful rechunk all documents."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_kb.id = 1

        mock_doc1 = MagicMock()
        mock_doc1.id = 1
        mock_doc1.content_text = "Content 1"

        mock_doc2 = MagicMock()
        mock_doc2.id = 2
        mock_doc2.content_text = "Content 2"

        mock_doc3 = MagicMock()
        mock_doc3.id = 3
        mock_doc3.content_text = None  # No content

        def execute_side_effect(stmt):
            mock_result = MagicMock()
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1
            if execute_side_effect.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_kb
            else:
                mock_result.scalars.return_value.all.return_value = [mock_doc1, mock_doc2, mock_doc3]
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        with patch.object(
            KnowledgeBaseEditService, 'rechunk_document',
            side_effect=[
                (MagicMock(), 5, None),  # doc1 success
                (None, 0, "Error"),      # doc2 fails
            ]
        ):
            success, failed, err = KnowledgeBaseEditService.rechunk_all_documents(mock_db, 1)
            assert success == 1
            assert failed == 2  # doc2 failed, doc3 skipped (no content)
            assert err is None

    def test_rechunk_all_documents_empty(self):
        """Test rechunk all when no documents."""
        from app.services.knowledge_base_edit_service import KnowledgeBaseEditService

        mock_db = MagicMock()
        mock_kb = MagicMock()
        mock_kb.id = 1

        def execute_side_effect(stmt):
            mock_result = MagicMock()
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1
            if execute_side_effect.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_kb
            else:
                mock_result.scalars.return_value.all.return_value = []
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        success, failed, err = KnowledgeBaseEditService.rechunk_all_documents(mock_db, 1)
        assert success == 0
        assert failed == 0
        assert err is None
