"""Authentication APIs."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.limiter import limiter
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TotpSetupRequest, TotpVerifyRequest
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """Login with username and password."""
    user = AuthService.authenticate_user(db, payload.username, payload.password)
    if user is None:
        return {"code": 1002, "message": "认证失败", "detail": "用户名或密码错误"}

    if user.totp_secret:
        if payload.totp_code is None:
            return {"code": 1002, "message": "认证失败", "detail": "请提供 TOTP 验证码"}
        if not AuthService.verify_totp_code(user.totp_secret, payload.totp_code):
            return {"code": 1002, "message": "认证失败", "detail": "TOTP 验证失败"}

    token = create_access_token(subject=user.username)
    return {
        "code": 0,
        "message": "success",
        "data": {"access_token": token, "token_type": "bearer"},
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Return current user info for SPA token validation (id, username, non-sensitive only)."""
    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "role": getattr(current_user, "role", "viewer"),
            "is_admin": getattr(current_user, "is_admin", False),
        },
    }


@router.post("/logout")
def logout() -> dict:
    """Stateless logout endpoint."""
    return {"code": 0, "message": "success", "data": {"logged_out": True}}


@router.post("/totp/setup")
def totp_setup(payload: TotpSetupRequest, db: Session = Depends(get_db)) -> dict:
    """Generate TOTP secret and provisioning URI."""
    user = AuthService.authenticate_user(db, payload.username, payload.password)
    if user is None:
        return {"code": 1002, "message": "认证失败", "detail": "用户名或密码错误"}

    secret = AuthService.generate_totp_secret()
    uri = AuthService.build_totp_uri(username=user.username, secret=secret)
    return {"code": 0, "message": "success", "data": {"secret": secret, "otpauth_url": uri}}


@router.post("/totp/verify")
def totp_verify(payload: TotpVerifyRequest, db: Session = Depends(get_db)) -> dict:
    """Verify TOTP code and bind secret to user."""
    user = AuthService.authenticate_user(db, payload.username, payload.password)
    if user is None:
        return {"code": 1002, "message": "认证失败", "detail": "用户名或密码错误"}

    if not AuthService.verify_totp_code(payload.secret, payload.code):
        return {"code": 1002, "message": "认证失败", "detail": "TOTP 验证失败"}

    AuthService.save_totp_secret(db, user, payload.secret)
    return {"code": 0, "message": "success", "data": {"totp_enabled": True}}

