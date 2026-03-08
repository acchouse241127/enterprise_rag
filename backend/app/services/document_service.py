"""Document domain service."""

import hashlib
import logging
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.document_parser import content_list_to_chunks, get_parser_for_extension
from app.models import Document, KnowledgeBase
from app.rag import BgeM3EmbeddingService, ChromaVectorStore, TextChunker
from app.rag.chunker import ChunkMode

logger = logging.getLogger(__name__)

# B3.1: 文件类型到分块模式的映射
# 文档类型（pdf/docx/txt/md）使用 sentence 模式，保持语义完整性
# 表格/演示类型（xlsx/pptx）使用 char 模式，因为内容较短且结构化
FILE_TYPE_CHUNK_MODE: dict[str, ChunkMode] = {
    # 文档类型 → sentence 模式
    "pdf": "sentence",
    "docx": "sentence",
    "doc": "sentence",
    "txt": "sentence",
    "md": "sentence",
    "markdown": "sentence",
    "html": "sentence",
    "htm": "sentence",
    # 表格/演示类型 → char 模式
    "xlsx": "char",
    "xls": "char",
    "pptx": "char",
    "ppt": "char",
    # 音视频/图片 → 默认 sentence（内容通常是从转录/OCR提取的文字）
    "mp3": "sentence",
    "wav": "sentence",
    "mp4": "sentence",
    "webm": "sentence",
    "png": "sentence",
    "jpg": "sentence",
    "jpeg": "sentence",
    # URL → sentence
    "url": "sentence",
}


def get_chunk_mode_for_file(filename: str, file_type: str | None = None) -> ChunkMode:
    """
    根据文件类型返回推荐的分块模式。

    Args:
        filename: 文件名（用于提取扩展名）
        file_type: 文件类型（可选，优先使用）

    Returns:
        ChunkMode: 'sentence' 或 'char'
    """
    # 先检查 file_type
    if file_type and file_type in FILE_TYPE_CHUNK_MODE:
        return FILE_TYPE_CHUNK_MODE[file_type]

    # 再检查扩展名
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix in FILE_TYPE_CHUNK_MODE:
        return FILE_TYPE_CHUNK_MODE[suffix]

    # 默认使用 sentence 模式
    return "sentence"


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
    def _get_chunker(
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> TextChunker:
        """Get chunker with optional custom parameters (B3.2)."""
        return TextChunker(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap,
        )

    @staticmethod
    def _chunk_text(
        text: str,
        filename: str,
        file_type: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> list[str]:
        """
        Chunk text using appropriate mode for file type (B3.1).

        Args:
            text: Text to chunk
            filename: Original filename (for determining chunk mode)
            file_type: File type (optional)
            chunk_size: Custom chunk size (B3.2)
            chunk_overlap: Custom chunk overlap (B3.2)

        Returns:
            List of text chunks
        """
        chunker = DocumentService._get_chunker(chunk_size, chunk_overlap)
        mode = get_chunk_mode_for_file(filename, file_type)
        chunks = chunker.chunk(text, mode=mode)
        logger.debug(
            "Chunked %s with mode=%s, chunks=%d",
            filename,
            mode,
            len(chunks),
        )
        return chunks

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
    def _process_parsed_contents(
        contents,  # list[ParsedContent]
        doc: Document,
        kb_chunk_size: int | None,
        kb_chunk_overlap: int | None,
    ) -> tuple[list[str], str]:
        """
        Process parsed contents into chunks.

        Uses the new content_list_to_chunks converter to preserve
        type prefixes like [表格], [图片], [公式].

        Args:
            contents: List of ParsedContent from parser
            doc: Document model instance
            kb_chunk_size: KB-level chunk size override
            kb_chunk_overlap: KB-level chunk overlap override

        Returns:
            Tuple of (chunks list, content_text string)
        """
        # Convert ParsedContent list to text chunks with type prefixes
        raw_chunks = content_list_to_chunks(contents, include_type_prefix=True)

        # Combine for content_text storage
        content_text = "\n\n".join(raw_chunks)

        # Further chunk if needed (for very long documents)
        final_chunks = DocumentService._chunk_text(
            content_text,
            doc.filename,
            doc.file_type,
            kb_chunk_size,
            kb_chunk_overlap,
        )

        return final_chunks, content_text

    @staticmethod
    def parse_and_index_sync(db: Session, document_id: int) -> None:
        """
        Parse document, chunk, embed, upsert to vector store; update doc status.
        Used by Celery worker task. Caller must provide a dedicated session.
        """
        doc = DocumentService.get_by_id(db, document_id)
        if doc is None:
            return

        # B3.2: 获取 KB 级分块配置
        kb = db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == doc.knowledge_base_id)
        ).scalar_one_or_none()
        kb_chunk_size = kb.chunk_size if kb else None
        kb_chunk_overlap = kb.chunk_overlap if kb else None

        if doc.file_type == "url":
            from app.document_parser.url_parser import UrlParser
            parser = UrlParser()
            contents = parser.parse_url(doc.file_path)
            # URL parser returns list[ParsedContent]
            doc.status = "parsing"
            doc.parser_message = "抓取中"
            db.add(doc)
            db.commit()
            try:
                chunks, content_text = DocumentService._process_parsed_contents(
                    contents, doc, kb_chunk_size, kb_chunk_overlap
                )
                doc.content_text = content_text
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
                        doc.parser_message = f"抓取成功，分块 {len(chunks)}，向量化完成"
                    else:
                        doc.status = "parsed"
                        doc.parser_message = f"抓取成功，向量化跳过: {err}"
                else:
                    doc.status = "parsed"
                    doc.parser_message = "抓取成功，但未生成有效分块"
            except Exception as exc:
                doc.status = "parse_failed"
                doc.parser_message = f"抓取失败: {exc}"
            db.add(doc)
            db.commit()
            return

        path = Path(doc.file_path)
        if not path.exists():
            doc.status = "parse_failed"
            doc.parser_message = "文件不存在"
            db.add(doc)
            db.commit()
            return
        suffix = Path(doc.filename).suffix.lower()
        parser = get_parser_for_extension(suffix)
        knowledge_base_id = doc.knowledge_base_id
        doc.status = "parsing"
        doc.parser_message = "解析中"
        db.add(doc)
        db.commit()
        db.refresh(doc)

        if parser is None:
            doc.status = "parser_not_implemented"
            doc.parser_message = f"{suffix} 解析器尚未实现"
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return
        try:
            # New interface: parse() returns list[ParsedContent]
            contents = parser.parse(path)
            chunks, content_text = DocumentService._process_parsed_contents(
                contents, doc, kb_chunk_size, kb_chunk_overlap
            )
            doc.content_text = content_text
            doc.status = "parsed"
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

    @staticmethod
    def _validate_kb_exists(db: Session, knowledge_base_id: int) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_from_url(
        db: Session, knowledge_base_id: int, url: str, created_by: int | None
    ) -> tuple[Document | None, str | None]:
        """Create a document record from URL; worker will fetch and index."""
        from urllib.parse import urlparse
        kb = DocumentService._validate_kb_exists(db, knowledge_base_id)
        if kb is None:
            return None, "知识库不存在"
        url = (url or "").strip()
        if not url.startswith(("http://", "https://")):
            return None, "请输入有效的 http(s) URL"
        try:
            parsed = urlparse(url)
            title = parsed.netloc or url[:50]
        except Exception:
            title = url[:50]
        file_hash = hashlib.sha256(url.encode()).hexdigest()
        filename = url[:500] if len(url) <= 500 else url[:497] + "..."
        doc = Document(
            knowledge_base_id=knowledge_base_id,
            title=title,
            filename=filename,
            file_path=url,
            file_type="url",
            file_size=0,
            file_hash=file_hash,
            status="pending",
            parser_message="已入队，等待抓取",
            version=1,
            parent_document_id=None,
            is_current=True,
            created_by=created_by,
            source_url=url,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc, None

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
        allowed_suffixes = {
            ".txt", ".md", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".png", ".jpg", ".jpeg",
            ".mp3", ".wav", ".m4a", ".flac", ".mp4", ".webm", ".mov",
        }
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
            status="pending",
            parser_message="已入队，等待解析",
            version=version,
            parent_document_id=parent_document_id,
            is_current=True,
            created_by=created_by,
        )
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

        # URL 文档：file_path 存的是 URL 字符串，不入本地路径判断，直接入队
        if getattr(doc, "file_type", None) == "url":
            from app.tasks.document_tasks import parse_and_index
            doc.status = "parsing"
            doc.parser_message = "已入队，等待重新解析"
            db.add(doc)
            db.commit()
            db.refresh(doc)
            parse_and_index.delay(document_id)
            return doc, None

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
            # New interface: parse() returns list[ParsedContent]
            contents = parser.parse(path)
            chunks, content_text = DocumentService._process_parsed_contents(
                contents, doc, None, None
            )
            doc.content_text = content_text
            doc.status = "parsed"
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
            chunks = DocumentService._chunk_text(target_doc.content_text, target_doc.filename, target_doc.file_type)
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
