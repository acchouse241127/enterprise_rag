"""Document domain service."""

import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.document_parser import get_parser_for_extension
from app.models import Document, KnowledgeBase
from app.rag import BgeM3EmbeddingService, ChromaVectorStore, TextChunker


class DocumentService:
    """Document upload, versioning, and parse service."""
    _chunker = TextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
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
    def list_by_kb(db: Session, knowledge_base_id: int) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .order_by(desc(Document.created_at))
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_id(db: Session, document_id: int) -> Document | None:
        stmt = select(Document).where(Document.id == document_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def _validate_kb_exists(db: Session, knowledge_base_id: int) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    async def upload(
        db: Session, knowledge_base_id: int, upload_file: UploadFile, created_by: int | None
    ) -> tuple[Document | None, str | None]:
        kb = DocumentService._validate_kb_exists(db, knowledge_base_id)
        if kb is None:
            return None, "知识库不存在"

        if not upload_file.filename:
            return None, "文件名不能为空"

        suffix = Path(upload_file.filename).suffix.lower()
        allowed_suffixes = {".txt", ".md", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".png", ".jpg", ".jpeg"}
        if suffix not in allowed_suffixes:
            return None, f"不支持的文件类型: {suffix}"

        content = await upload_file.read()
        if len(content) > settings.max_file_size_mb * 1024 * 1024:
            return None, f"文件大小超过 {settings.max_file_size_mb}MB 限制"
        if len(content) == 0:
            return None, "文件内容为空"

        storage_root = Path(settings.upload_root_dir)
        # 按用户独立存储：user_{user_id}/kb_{kb_id}，created_by 为空时用 0（如文件夹同步）
        user_prefix = f"user_{created_by or 0}"
        storage_dir = storage_root / user_prefix / f"kb_{knowledge_base_id}"
        storage_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_name = Path(upload_file.filename).name
        storage_path = storage_dir / f"{timestamp}_{safe_name}"
        storage_path.write_bytes(content)

        file_hash = hashlib.sha256(content).hexdigest()
        title = Path(safe_name).stem

        stmt = (
            select(Document)
            .where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.filename == safe_name,
                Document.is_current.is_(True),
            )
            .order_by(desc(Document.version))
        )
        latest = db.execute(stmt).scalars().first()
        version = 1
        parent_document_id = None
        if latest is not None:
            latest.is_current = False
            db.add(latest)
            version = latest.version + 1
            parent_document_id = latest.id

        doc = Document(
            knowledge_base_id=knowledge_base_id,
            title=title,
            filename=safe_name,
            file_path=str(storage_path.resolve()),
            file_type=suffix.removeprefix("."),
            file_size=len(content),
            file_hash=file_hash,
            status="uploaded",
            parser_message=None,
            version=version,
            parent_document_id=parent_document_id,
            is_current=True,
            created_by=created_by,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        parser = get_parser_for_extension(suffix)
        if parser is None:
            doc.status = "parser_not_implemented"
            doc.parser_message = f"{suffix} 解析器尚未实现"
        else:
            try:
                parsed_text = parser.parse(storage_path)
                doc.content_text = parsed_text
                doc.status = "parsed"
                doc.parser_message = "解析成功"
                chunks = DocumentService._chunker.chunk(parsed_text)
                if chunks:
                    embeddings = DocumentService._embedding_service.embed(chunks)
                    ok, err = DocumentService._vector_store.upsert_document_chunks(
                        knowledge_base_id=knowledge_base_id,
                        document_id=doc.id,
                        chunks=chunks,
                        embeddings=embeddings,
                    )
                    if ok:
                        doc.status = "vectorized"
                        doc.parser_message = f"解析成功，分块 {len(chunks)}，向量化完成"
                    else:
                        doc.status = "parsed"
                        doc.parser_message = f"解析成功，分块 {len(chunks)}，向量化跳过: {err}"
                else:
                    doc.parser_message = "解析成功，但未生成有效分块"
            except Exception as exc:
                doc.status = "parse_failed"
                doc.parser_message = f"解析失败: {exc}"

        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc, None

    @staticmethod
    def reparse(db: Session, document_id: int) -> tuple[Document | None, str | None]:
        """Re-parse and re-vectorize an existing document by id."""
        doc = DocumentService.get_by_id(db, document_id)
        if doc is None:
            return None, "文档不存在"

        path = Path(doc.file_path)
        if not path.exists():
            return None, "文件不存在"

        suffix = Path(doc.filename).suffix.lower()
        parser = get_parser_for_extension(suffix)
        if parser is None:
            doc.status = "parser_not_implemented"
            doc.parser_message = f"{suffix} 解析器尚未实现"
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return doc, None

        try:
            parsed_text = parser.parse(path)
            doc.content_text = parsed_text
            doc.status = "parsed"
            doc.parser_message = "解析成功"
            chunks = DocumentService._chunker.chunk(parsed_text)
            if chunks:
                embeddings = DocumentService._embedding_service.embed(chunks)
                ok, err = DocumentService._vector_store.upsert_document_chunks(
                    knowledge_base_id=doc.knowledge_base_id,
                    document_id=doc.id,
                    chunks=chunks,
                    embeddings=embeddings,
                )
                if ok:
                    doc.status = "vectorized"
                    doc.parser_message = f"解析成功，分块 {len(chunks)}，向量化完成"
                else:
                    doc.status = "parsed"
                    doc.parser_message = f"解析成功，分块 {len(chunks)}，向量化跳过: {err}"
            else:
                doc.parser_message = "解析成功，但未生成有效分块"
        except Exception as exc:
            doc.status = "parse_failed"
            doc.parser_message = f"解析失败: {exc}"

        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc, None

    @staticmethod
    def delete(db: Session, doc: Document) -> None:
        db.delete(doc)
        db.commit()

    # ========== 版本管理 ==========

    @staticmethod
    def list_versions(db: Session, document_id: int) -> tuple[list[Document], str | None]:
        """
        列出文档的所有版本（包括当前版本和历史版本）。
        通过 filename + knowledge_base_id 查找同一文档的所有版本。
        """
        doc = DocumentService.get_by_id(db, document_id)
        if doc is None:
            return [], "文档不存在"

        stmt = (
            select(Document)
            .where(
                Document.knowledge_base_id == doc.knowledge_base_id,
                Document.filename == doc.filename,
            )
            .order_by(desc(Document.version))
        )
        versions = list(db.execute(stmt).scalars().all())
        return versions, None

    @staticmethod
    def activate_version(db: Session, document_id: int) -> tuple[Document | None, str | None]:
        """
        激活指定版本为当前版本。
        1. 将同文档其他版本的 is_current 设为 False
        2. 将指定版本的 is_current 设为 True
        3. 同步向量库：删除旧当前版本向量，添加新当前版本向量
        """
        target_doc = DocumentService.get_by_id(db, document_id)
        if target_doc is None:
            return None, "文档不存在"

        if target_doc.is_current:
            return target_doc, None  # 已经是当前版本，无需操作

        # 查找当前版本
        stmt = (
            select(Document)
            .where(
                Document.knowledge_base_id == target_doc.knowledge_base_id,
                Document.filename == target_doc.filename,
                Document.is_current.is_(True),
            )
        )
        current_doc = db.execute(stmt).scalar_one_or_none()

        # 1. 删除旧当前版本的向量
        if current_doc is not None:
            current_doc.is_current = False
            db.add(current_doc)
            # 删除旧版本向量
            DocumentService._vector_store.delete_document_chunks(
                knowledge_base_id=current_doc.knowledge_base_id,
                document_id=current_doc.id,
            )

        # 2. 设置新当前版本
        target_doc.is_current = True
        db.add(target_doc)

        # 3. 为新当前版本重新生成向量（如果有解析内容）
        if target_doc.content_text:
            chunks = DocumentService._chunker.chunk(target_doc.content_text)
            if chunks:
                embeddings = DocumentService._embedding_service.embed(chunks)
                ok, err = DocumentService._vector_store.upsert_document_chunks(
                    knowledge_base_id=target_doc.knowledge_base_id,
                    document_id=target_doc.id,
                    chunks=chunks,
                    embeddings=embeddings,
                )
                if ok:
                    target_doc.status = "vectorized"
                    target_doc.parser_message = f"版本切换，分块 {len(chunks)}，向量化完成"
                else:
                    target_doc.status = "parsed"
                    target_doc.parser_message = f"版本切换，分块 {len(chunks)}，向量化跳过: {err}"
                db.add(target_doc)

        db.commit()
        db.refresh(target_doc)
        return target_doc, None

