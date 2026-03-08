"""API dependency providers."""

from collections.abc import Generator
from typing import Annotated, Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import RoleEnum, User


def get_db() -> Generator:
    """Provide database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate JWT token from Authorization header.
    Returns current user or raises 401 Unauthorized.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if authorization is None:
        raise credentials_exception

    # Support "Bearer <token>" format
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    elif len(parts) == 1:
        token = parts[0]
    else:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User | None:
    """
    Optional authentication - returns user if valid token provided, None otherwise.
    Useful for endpoints that work with or without authentication.
    """
    if authorization is None:
        return None

    try:
        return get_current_user(authorization=authorization, db=db)
    except HTTPException:
        return None


# ========== RBAC Permission Dependencies (Phase 2.3) ==========

def require_permission(permission: str) -> Callable:
    """
    Dependency factory to require a specific permission.
    
    Usage:
        @router.post("/admin-only")
        def admin_endpoint(user: User = Depends(require_permission("admin"))):
            ...
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {permission} 权限",
            )
        return current_user
    return permission_checker


def require_role(*roles: RoleEnum) -> Callable:
    """
    Dependency factory to require specific role(s).
    
    Usage:
        @router.delete("/kb/{kb_id}")
        def delete_kb(user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.EDITOR))):
            ...
    """
    role_values = {r.value for r in roles}

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {', '.join(role_values)} 角色",
            )
        return current_user
    return role_checker


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that requires admin role."""
    if current_user.role != RoleEnum.ADMIN.value and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要管理员权限",
        )
    return current_user


def get_editor_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that requires editor or admin role."""
    if current_user.role not in (RoleEnum.ADMIN.value, RoleEnum.EDITOR.value) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要编辑者或管理员权限",
        )
    return current_user


# ========== Service Layer Dependencies (Repository Pattern) ==========

import functools


@functools.cache
def get_conversation_store():
    """Get or create the singleton conversation store."""
    from app.services.conversation_store import create_conversation_store
    return create_conversation_store()


@functools.cache
def get_qa_service():
    """Get or create the singleton QaService instance.
    
    This factory creates a QaService with all dependencies injected,
    following the Repository Pattern for better testability and maintainability.
    """
    from app.rag import (
        BgeM3EmbeddingService,
        BgeRerankerService,
        ChromaVectorStore,
        RagPipeline,
        VectorRetriever,
    )
    from app.rag.keyword_retriever import KeywordRetriever
    from app.services.qa_service import QaService

    # Create dependencies
    embedding_service = BgeM3EmbeddingService(
        model_name=settings.embedding_model_name,
        fallback_dim=settings.embedding_fallback_dim,
    )
    vector_store = ChromaVectorStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_prefix=settings.chroma_collection_prefix,
    )
    retriever = VectorRetriever(embedding_service, vector_store)
    keyword_retriever = KeywordRetriever(embedding_service, vector_store)
    reranker = BgeRerankerService(model_name=settings.reranker_model_name)
    pipeline = RagPipeline(retriever, embedding_service)
    conversation_store = get_conversation_store()

    return QaService(
        retriever=retriever,
        embedding_service=embedding_service,
        vector_store=vector_store,
        reranker=reranker,
        pipeline=pipeline,
        keyword_retriever=keyword_retriever,
        conversation_store=conversation_store,
    )


@functools.cache
def get_document_service():
    """Get or create the singleton DocumentService instance."""
    from app.services.document_service import DocumentService
    return DocumentService()

