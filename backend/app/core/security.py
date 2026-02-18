"""
Security utilities for password hash and JWT.

Author: C2
Date: 2026-02-13
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# bcrypt 最大支持 72 字节，超出需截断（避免 passlib 与 bcrypt 4.1+ 兼容性问题，直接用 bcrypt 库）
BCRYPT_MAX_PASSWORD_BYTES = 72


def _to_bcrypt_bytes(password: str) -> bytes:
    """Encode password to bytes, truncate to 72 bytes for bcrypt."""
    raw = password.encode("utf-8")
    return raw[:BCRYPT_MAX_PASSWORD_BYTES] if len(raw) > BCRYPT_MAX_PASSWORD_BYTES else raw


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return bcrypt.hashpw(_to_bcrypt_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify plain password against bcrypt hash."""
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain_password), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str) -> str:
    """Create access JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """Decode JWT token payload."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None

