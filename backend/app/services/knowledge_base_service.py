"""Knowledge base domain service."""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Document, KnowledgeBase, FolderSyncConfig

logger = logging.getLogger(__name__)
from app.schemas import KnowledgeBaseCreateRequest, KnowledgeBaseUpdateRequest


class KnowledgeBaseService:
    """Knowledge base CRUD service."""

    @staticmethod
    def list_all(
        db: Session,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> list[KnowledgeBase]:
        """OPT-026: 支持按 created_at / name 排序，order 为 asc 或 desc。"""
        order_col = KnowledgeBase.created_at
        if sort_by == "name":
            order_col = KnowledgeBase.name
        if order and order.lower() == "asc":
            stmt = select(KnowledgeBase).order_by(order_col.asc())
        else:
            stmt = select(KnowledgeBase).order_by(order_col.desc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_document_count(db: Session, knowledge_base_id: int) -> int:
        """Get document count for a knowledge base."""
        stmt = select(func.count()).select_from(Document).where(
            Document.knowledge_base_id == knowledge_base_id
        )
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def list_all_with_doc_count(
        db: Session,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> list[dict]:
        """List all knowledge bases with document count. OPT-026: 支持排序。"""
        kbs = KnowledgeBaseService.list_all(db, sort_by=sort_by, order=order)
        result = []
        for kb in kbs:
            doc_count = KnowledgeBaseService.get_document_count(db, kb.id)
            result.append({
                "kb": kb,
                "document_count": doc_count,
            })
        return result

    @staticmethod
    def get_documents(db: Session, knowledge_base_id: int) -> list[Document]:
        """Get all documents in a knowledge base."""
        stmt = select(Document).where(
            Document.knowledge_base_id == knowledge_base_id
        ).order_by(Document.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_id(db: Session, knowledge_base_id: int) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_name(db: Session, name: str) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.name == name)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(db: Session, payload: KnowledgeBaseCreateRequest, created_by: int | None = None) -> KnowledgeBase:
        kb = KnowledgeBase(
            name=payload.name.strip(),
            description=payload.description,
            created_by=created_by or payload.created_by,
            # V2.0 新增字段
            chunk_size=payload.chunk_size,
            chunk_overlap=payload.chunk_overlap,
            chunk_mode=payload.chunk_mode,
            parent_retrieval_mode=payload.parent_retrieval_mode,
            dynamic_expand_n=payload.dynamic_expand_n,
            default_retrieval_strategy=payload.default_retrieval_strategy,
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return kb

    @staticmethod
    def update(
        db: Session, kb: KnowledgeBase, payload: KnowledgeBaseUpdateRequest
    ) -> KnowledgeBase:
        if payload.name is not None:
            kb.name = payload.name.strip()
        if payload.description is not None:
            kb.description = payload.description
        # V2.0 新增字段
        if payload.chunk_size is not None:
            kb.chunk_size = payload.chunk_size
        if payload.chunk_overlap is not None:
            kb.chunk_overlap = payload.chunk_overlap
        if payload.chunk_mode is not None:
            kb.chunk_mode = payload.chunk_mode
        if payload.parent_retrieval_mode is not None:
            kb.parent_retrieval_mode = payload.parent_retrieval_mode
        if payload.dynamic_expand_n is not None:
            kb.dynamic_expand_n = payload.dynamic_expand_n
        # V2.0: 默认检索策略
        if payload.default_retrieval_strategy is not None:
            kb.default_retrieval_strategy = payload.default_retrieval_strategy
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return kb

    @staticmethod
    def delete(db: Session, kb: KnowledgeBase) -> tuple[bool, str | None]:
        """删除知识库及关联数据。Chroma 失败仅记录并继续；DB 失败时 rollback 并返回错误信息。"""
        kb_id, kb_name = kb.id, kb.name
        doc_stmt = select(Document).where(Document.knowledge_base_id == kb_id)
        documents = list(db.execute(doc_stmt).scalars().all())

        # 1) Chroma：按文档逐个清理，任一失败只打日志不中断
        # 直接使用 ChromaVectorStore 避免循环导入 DocumentService
        from app.rag import ChromaVectorStore
        from app.config import settings
        vector_store = ChromaVectorStore(
            host=settings.chroma_host,
            port=settings.chroma_port,
            collection_prefix=settings.chroma_collection_prefix,
        )
        for doc in documents:
            try:
                ok, err = vector_store.delete_document_chunks(
                    knowledge_base_id=kb_id,
                    document_id=doc.id,
                )
                if not ok and err:
                    logger.warning("Chroma delete doc kb_id=%s doc_id=%s: %s", kb_id, doc.id, err)
            except Exception as e:
                logger.warning(
                    "Chroma delete_document_chunks exception kb_id=%s doc_id=%s: %s",
                    kb_id, doc.id, e,
                    exc_info=True,
                )

        # 2) DB：先删同步配置，再解除文档自引用，再删文档与知识库
        try:
            # 显式删除文件夹同步配置，避免 cascade 顺序问题
            sync_rows = list(db.execute(select(FolderSyncConfig).where(FolderSyncConfig.knowledge_base_id == kb_id)).scalars().all())
            for cfg in sync_rows:
                db.delete(cfg)
            # 解除 Document 自引用，否则无法删父文档
            for doc in documents:
                doc.parent_document_id = None
                db.add(doc)
            db.flush()
            for doc in documents:
                db.delete(doc)
            db.delete(kb)
            db.commit()
            logger.info("Knowledge base deleted: id=%s name=%s", kb_id, kb_name)
            return True, None
        except Exception as e:
            db.rollback()
            logger.exception("Knowledge base delete failed: id=%s", kb_id)
            return False, f"{type(e).__name__}: {e}"

