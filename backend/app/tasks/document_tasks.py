"""Celery tasks for document parse and index."""

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.document_service import DocumentService


@celery_app.task(bind=True)
def parse_and_index(self, document_id: int) -> dict:
    """
    Async task: parse document, chunk, embed, upsert to vector store.
    Updates Document status and parser_message in DB.
    """
    db = SessionLocal()
    try:
        DocumentService.parse_and_index_sync(db, document_id)
        return {"document_id": document_id, "status": "ok"}
    except Exception as exc:
        db.rollback()
        doc = DocumentService.get_by_id(db, document_id)
        if doc is not None:
            doc.status = "parse_failed"
            doc.parser_message = f"任务执行异常: {exc}"
            db.add(doc)
            db.commit()
        raise
    finally:
        db.close()
