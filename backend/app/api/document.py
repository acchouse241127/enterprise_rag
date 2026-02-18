"""Document APIs."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas import DocumentData
from app.services.document_service import DocumentService
from app.tasks.document_tasks import parse_and_index

router = APIRouter()


@router.get("/knowledge-bases/{knowledge_base_id}/documents")
def list_documents(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List documents in a knowledge base."""
    items = DocumentService.list_by_kb(db, knowledge_base_id)
    data = [DocumentData.model_validate(item).model_dump(mode="json") for item in items]
    return {"code": 0, "message": "success", "data": data}


@router.post("/knowledge-bases/{knowledge_base_id}/documents")
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload a document and trigger base parsing."""
    doc, err = await DocumentService.upload(
        db=db, knowledge_base_id=knowledge_base_id, upload_file=file, created_by=current_user.id
    )
    if err is not None:
        return {"code": 1001, "message": "参数错误", "detail": err}
    parse_and_index.delay(doc.id)
    return {
        "code": 0,
        "message": "success",
        "data": DocumentData.model_validate(doc).model_dump(mode="json"),
    }


@router.post("/knowledge-bases/{knowledge_base_id}/documents/batch")
async def batch_upload_documents(
    knowledge_base_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Batch upload documents."""
    if not files:
        return {"code": 1001, "message": "参数错误", "detail": "至少上传一个文件"}

    success_items: list[dict] = []
    failed_items: list[dict] = []
    for item in files:
        doc, err = await DocumentService.upload(
            db=db, knowledge_base_id=knowledge_base_id, upload_file=item, created_by=current_user.id
        )
        if err is None and doc is not None:
            parse_and_index.delay(doc.id)
            success_items.append(DocumentData.model_validate(doc).model_dump(mode="json"))
        else:
            failed_items.append({"filename": item.filename, "error": err or "上传失败"})

    if failed_items:
        message = "partial_success" if success_items else "failed"
    else:
        message = "success"
    return {
        "code": 0,
        "message": message,
        "data": {
            "total": len(files),
            "success_count": len(success_items),
            "failed_count": len(failed_items),
            "success_items": success_items,
            "failed_items": failed_items,
        },
    }


@router.get("/documents/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get document metadata by id."""
    doc = DocumentService.get_by_id(db, document_id)
    if doc is None:
        return {"code": 4040, "message": "资源不存在", "detail": "文档不存在"}
    return {
        "code": 0,
        "message": "success",
        "data": DocumentData.model_validate(doc).model_dump(mode="json"),
    }


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download original uploaded file. Returns 404 if doc or file not found (so client does not save JSON as file)."""
    doc = DocumentService.get_by_id(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(path=file_path, filename=doc.filename)


@router.post("/documents/{document_id}/reparse")
def reparse_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Re-parse and re-vectorize document."""
    doc, err = DocumentService.reparse(db, document_id)
    if err is not None:
        return {"code": 4001, "message": "重新解析失败", "detail": err}
    return {
        "code": 0,
        "message": "success",
        "data": DocumentData.model_validate(doc).model_dump(mode="json"),
    }


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete document record."""
    doc = DocumentService.get_by_id(db, document_id)
    if doc is None:
        return {"code": 4040, "message": "资源不存在", "detail": "文档不存在"}
    DocumentService.delete(db, doc)
    return {"code": 0, "message": "success", "data": {"deleted": True}}


@router.get("/documents/{document_id}/preview")
def preview_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get document parsed content for preview."""
    doc = DocumentService.get_by_id(db, document_id)
    if doc is None:
        return {"code": 4040, "message": "资源不存在", "detail": "文档不存在"}

    # 返回解析后的内容 (字段名是 content_text)
    content = doc.content_text or ""
    if not content and doc.status in ("pending", "parsing"):
        content = "（文档正在解析中，请稍后刷新...）"
    elif not content and doc.status == "parse_failed":
        content = f"（文档解析失败：{doc.parser_message or '未知错误'}）"
    elif not content:
        content = "（暂无解析内容）"

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "content": content,
        },
    }


# ========== 版本管理 API ==========


@router.get("/documents/{document_id}/versions")
def list_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    获取文档的所有版本历史。
    返回同一文档（filename + knowledge_base_id）的所有版本列表，按版本号降序排列。
    """
    versions, err = DocumentService.list_versions(db, document_id)
    if err is not None:
        return {"code": 4040, "message": "资源不存在", "detail": err}
    data = [DocumentData.model_validate(v).model_dump(mode="json") for v in versions]
    return {"code": 0, "message": "success", "data": data}


@router.post("/documents/{document_id}/activate")
def activate_document_version(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    激活指定版本为当前版本。
    将该版本设为 is_current=True，其他版本设为 is_current=False。
    同时同步向量库：删除旧当前版本向量，添加新当前版本向量。
    """
    doc, err = DocumentService.activate_version(db, document_id)
    if err is not None:
        return {"code": 4001, "message": "版本切换失败", "detail": err}
    return {
        "code": 0,
        "message": "success",
        "data": DocumentData.model_validate(doc).model_dump(mode="json"),
    }

