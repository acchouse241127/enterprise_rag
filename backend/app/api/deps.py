"""API dependency providers."""

from collections.abc import Generator
from functools import wraps
from typing import Annotated, Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

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

