"""Authentication service."""

import pyotp
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User


class AuthService:
    """Auth domain service."""

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User | None:
        """Authenticate user by username and password."""
        stmt = select(User).where(User.username == username)
        user = db.execute(stmt).scalar_one_or_none()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def generate_totp_secret() -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    @staticmethod
    def build_totp_uri(username: str, secret: str, issuer: str = "EnterpriseRAG") -> str:
        """Create otpauth URI for authenticator apps."""
        return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)

    @staticmethod
    def verify_totp_code(secret: str, code: str) -> bool:
        """Verify one-time TOTP code."""
        return pyotp.TOTP(secret).verify(code, valid_window=1)

    @staticmethod
    def save_totp_secret(db: Session, user: User, secret: str) -> User:
        """Persist TOTP secret for user."""
        user.totp_secret = secret
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

