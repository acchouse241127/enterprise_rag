"""
创建默认管理员账号（若不存在）：admin / password123

使用方式（需先启动 PostgreSQL，在 backend 目录下）:
  python -m scripts.create_admin_user

或在 Docker 内：
  docker compose exec backend python -m scripts.create_admin_user
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"


def main():
    db = SessionLocal()
    try:
        existing = db.execute(select(User).where(User.username == ADMIN_USERNAME)).scalar_one_or_none()
        if existing:
            print(f"用户 {ADMIN_USERNAME} 已存在，无需创建。")
            return
        user = User(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            is_active=True,
            is_admin=True,
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"已创建管理员: username={ADMIN_USERNAME} 密码={ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
