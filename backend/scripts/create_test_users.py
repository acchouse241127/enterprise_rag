"""
创建 10 个测试账号（test1~test10），每个账号的上传文档会存到独立目录 user_{user_id}/kb_*。

使用方式（需先启动 PostgreSQL，在 enterprise_rag/backend 目录下）:
  python -m scripts.create_test_users

默认密码: Test123456
账号: test1, test2, ... test10（角色 viewer）
"""

import sys
from pathlib import Path

# 确保 backend 在 path 中
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User


DEFAULT_PASSWORD = "Test123456"


def main():
    db = SessionLocal()
    try:
        created = []
        for i in range(1, 11):
            username = f"test{i}"
            existing = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
            if existing:
                print(f"用户 {username} 已存在，跳过")
                continue
            user = User(
                username=username,
                password_hash=hash_password(DEFAULT_PASSWORD),
                is_active=True,
                is_admin=False,
                role="viewer",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created.append((user.id, username))
            print(f"已创建: id={user.id} username={username} 存储目录: user_{user.id}/")
        if created:
            print(f"\n共创建 {len(created)} 个测试账号。")
            print("用户名: test1 ~ test10，默认密码: Test123456")
            print("各账号上传的文档会保存在独立目录: data/uploads/user_{用户ID}/kb_*")
        else:
            print("未创建新用户（test1~test10 可能已存在）。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
