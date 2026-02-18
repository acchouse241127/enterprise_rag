"""
Database initialization script.
Creates tables and test user for Phase 1.1 testing.

Author: C2
Date: 2026-02-13
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models import User


def init_db() -> None:
    """Create tables and test user."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from sqlalchemy import select

        users_to_create = [
            ("admin", "password123", True),
            ("admin_totp", "password123", True),  # 用于 TOTP 测试，避免影响 admin
        ]
        for username, password, is_admin in users_to_create:
            stmt = select(User).where(User.username == username)
            if db.execute(stmt).scalar_one_or_none() is None:
                user = User(
                    username=username,
                    password_hash=hash_password(password),
                    is_active=True,
                    is_admin=is_admin,
                )
                db.add(user)
                db.commit()
                print(f"Test user created: {username} / {password}")
            else:
                print(f"Test user {username} already exists")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
