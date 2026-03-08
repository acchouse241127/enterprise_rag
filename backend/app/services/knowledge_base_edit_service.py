"""
Knowledge base editing service for content and chunk parameter adjustment.

Phase 3.3: 知识库在线编辑与分块调整
Author: C2
Date: 2026-02-14
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document, KnowledgeBase
from app.rag import BgeM3EmbeddingService, ChromaVectorStore, TextChunker

logger = logging.getLogger(__name__)


class KnowledgeBaseEditService:
    """Service for editing knowledge base content and chunk parameters."""

    _embedding_service = BgeM3EmbeddingService(
        model_name=settings.embedding_model_name,
        fallback_dim=settings.embedding_fallback_dim,
    )
    _vector_store = ChromaVectorStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_prefix=settings.chroma_collection_prefix,
    )

    @staticmethod
    def get_document_content(db: Session, document_id: int) -> tuple[Document | None, str | None]:
        """
        Get document content for editing.
        Returns (document, error_message).
        """
        stmt = select(Document).where(Document.id == document_id)
        doc = db.execute(stmt).scalar_one_or_none()
        if not doc:
            return None, "文档不存在"
        return doc, None

    @staticmethod
    def update_document_content(
        db: Session,
        document_id: int,
        new_content: str,
        updated_by: int | None = None,
    ) -> tuple[Document | None, str | None]:
        """
        Update document content and re-vectorize.
        Returns (document, error_message).
        """
        stmt = select(Document).where(Document.id == document_id)
        doc = db.execute(stmt).scalar_one_or_none()
        if not doc:
            return None, "文档不存在"

        if not new_content.strip():
            return None, "内容不能为空"

        # Get knowledge base for chunk settings
        kb_stmt = select(KnowledgeBase).where(KnowledgeBase.id == doc.knowledge_base_id)
        kb = db.execute(kb_stmt).scalar_one_or_none()

        # Determine chunk parameters
        chunk_size = kb.chunk_size if kb and kb.chunk_size else settings.chunk_size
        chunk_overlap = kb.chunk_overlap if kb and kb.chunk_overlap else settings.chunk_overlap

        # Create chunker with appropriate settings
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        try:
            # Delete old chunks from vector store
            KnowledgeBaseEditService._vector_store.delete_document_chunks(
                doc.knowledge_base_id, doc.id
            )

            # Update content
            doc.content_text = new_content
            doc.updated_at = datetime.now()

            # Re-chunk and vectorize
            chunks = chunker.chunk_text(new_content)
            if chunks:
                embeddings = KnowledgeBaseEditService._embedding_service.embed_texts(chunks)
                KnowledgeBaseEditService._vector_store.add_documents(
                    knowledge_base_id=doc.knowledge_base_id,
                    document_id=doc.id,
                    chunks=chunks,
                    embeddings=embeddings,
                )

            doc.status = "parsed"
            doc.parser_message = f"内容已更新，重新分块：{len(chunks)} 个块"
            db.commit()
            db.refresh(doc)
            return doc, None

        except Exception as e:
            logger.exception(f"Failed to update document content: {e}")
            db.rollback()
            return None, f"更新失败: {str(e)}"

    @staticmethod
    def get_kb_chunk_settings(db: Session, knowledge_base_id: int) -> dict | None:
        """Get current chunk settings for a knowledge base."""
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        kb = db.execute(stmt).scalar_one_or_none()
        if not kb:
            return None

        return {
            "knowledge_base_id": kb.id,
            "chunk_size": kb.chunk_size or settings.chunk_size,
            "chunk_overlap": kb.chunk_overlap or settings.chunk_overlap,
            "is_custom": kb.chunk_size is not None or kb.chunk_overlap is not None,
            "global_defaults": {
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
            },
        }

    @staticmethod
    def update_kb_chunk_settings(
        db: Session,
        knowledge_base_id: int,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> tuple[KnowledgeBase | None, str | None]:
        """
        Update chunk settings for a knowledge base.
        Set to None to use global defaults.
        """
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        kb = db.execute(stmt).scalar_one_or_none()
        if not kb:
            return None, "知识库不存在"

        # Validate chunk settings
        if chunk_size is not None:
            if chunk_size < 100 or chunk_size > 10000:
                return None, "chunk_size 必须在 100-10000 之间"
        if chunk_overlap is not None:
            if chunk_overlap < 0 or chunk_overlap > 500:
                return None, "chunk_overlap 必须在 0-500 之间"
            if chunk_size and chunk_overlap >= chunk_size:
                return None, "chunk_overlap 必须小于 chunk_size"

        kb.chunk_size = chunk_size
        kb.chunk_overlap = chunk_overlap
        kb.updated_at = datetime.now()
        db.commit()
        db.refresh(kb)
        return kb, None

    @staticmethod
    def rechunk_document(
        db: Session,
        document_id: int,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> tuple[Document | None, int, str | None]:
        """
        Re-chunk a document with new parameters.
        Returns (document, chunk_count, error_message).
        """
        stmt = select(Document).where(Document.id == document_id)
        doc = db.execute(stmt).scalar_one_or_none()
        if not doc:
            return None, 0, "文档不存在"

        if not doc.content_text:
            return None, 0, "文档内容为空，无法分块"

        # Get knowledge base for default chunk settings
        kb_stmt = select(KnowledgeBase).where(KnowledgeBase.id == doc.knowledge_base_id)
        kb = db.execute(kb_stmt).scalar_one_or_none()

        # Determine chunk parameters (priority: param > kb > global)
        final_chunk_size = chunk_size or (kb.chunk_size if kb and kb.chunk_size else settings.chunk_size)
        final_chunk_overlap = chunk_overlap or (kb.chunk_overlap if kb and kb.chunk_overlap else settings.chunk_overlap)

        # Validate
        if final_chunk_overlap >= final_chunk_size:
            return None, 0, "chunk_overlap 必须小于 chunk_size"

        chunker = TextChunker(chunk_size=final_chunk_size, chunk_overlap=final_chunk_overlap)

        try:
            # Delete old chunks
            KnowledgeBaseEditService._vector_store.delete_document_chunks(
                doc.knowledge_base_id, doc.id
            )

            # Re-chunk
            chunks = chunker.chunk_text(doc.content_text)
            if chunks:
                embeddings = KnowledgeBaseEditService._embedding_service.embed_texts(chunks)
                KnowledgeBaseEditService._vector_store.add_documents(
                    knowledge_base_id=doc.knowledge_base_id,
                    document_id=doc.id,
                    chunks=chunks,
                    embeddings=embeddings,
                )

            doc.parser_message = f"重新分块完成：{len(chunks)} 个块（size={final_chunk_size}, overlap={final_chunk_overlap}）"
            doc.updated_at = datetime.now()
            db.commit()
            db.refresh(doc)
            return doc, len(chunks), None

        except Exception as e:
            logger.exception(f"Failed to rechunk document: {e}")
            db.rollback()
            return None, 0, f"重新分块失败: {str(e)}"

    @staticmethod
    def rechunk_all_documents(
        db: Session,
        knowledge_base_id: int,
    ) -> tuple[int, int, str | None]:
        """
        Re-chunk all documents in a knowledge base using KB's chunk settings.
        Returns (success_count, failed_count, error_message).
        """
        kb_stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        kb = db.execute(kb_stmt).scalar_one_or_none()
        if not kb:
            return 0, 0, "知识库不存在"

        # Get all current documents
        doc_stmt = (
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .where(Document.is_current.is_(True))
        )
        documents = list(db.execute(doc_stmt).scalars().all())

        success_count = 0
        failed_count = 0

        for doc in documents:
            if not doc.content_text:
                failed_count += 1
                continue

            result, _, error = KnowledgeBaseEditService.rechunk_document(db, doc.id)
            if result:
                success_count += 1
            else:
                failed_count += 1
                logger.warning(f"Failed to rechunk document {doc.id}: {error}")

        return success_count, failed_count, None
