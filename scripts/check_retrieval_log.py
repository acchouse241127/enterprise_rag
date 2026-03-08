#!/usr/bin/env python3
"""
检索日志诊断脚本：检查 retrieval_log 相关配置与数据。

用法（在 enterprise_rag 目录下）:
  python scripts/check_retrieval_log.py

用途：排查「检索质量看板」无数据时的原因 3 和 4。
"""

import os
import sys

# 确保 backend 在 path 中
script_dir = os.path.dirname(os.path.abspath(__file__))
proj_root = os.path.dirname(script_dir)
backend_dir = os.path.join(proj_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.chdir(proj_root)


def main():
    print("=" * 60)
    print("检索日志诊断")
    print("=" * 60)

    # 1. 检查 RETRIEVAL_LOG_ENABLED
    from app.config import settings

    enabled = getattr(settings, "retrieval_log_enabled", True)
    env_val = os.getenv("RETRIEVAL_LOG_ENABLED", "(未设置)")
    print(f"\n1. RETRIEVAL_LOG_ENABLED")
    print(f"   环境变量值: {env_val}")
    print(f"   实际生效: {enabled}")
    if not enabled:
        print("   [X] 检索日志已关闭，看板无数据。请在 .env 中设置 RETRIEVAL_LOG_ENABLED=true 并重启后端。")
        return 1
    print("   [OK] 检索日志已启用")

    # 2. 检查 retrieval_logs 表
    try:
        from app.core.database import SessionLocal
        from app.models import RetrievalLog
        from sqlalchemy import select, func

        db = SessionLocal()
        try:
            count = db.execute(select(func.count(RetrievalLog.id))).scalar() or 0
            print(f"\n2. retrieval_logs 表")
            print(f"   总记录数: {count}")
            if count == 0:
                print("   [!] 表中无记录。请先完成至少一次 RAG 问答，再点击看板「刷新」。")
            else:
                print("   [OK] 有数据，看板应能显示")
        finally:
            db.close()
    except Exception as e:
        print(f"\n2. retrieval_logs 表")
        print(f"   [X] 数据库访问失败: {e}")
        print("   可能原因：retrieval_logs 表不存在（请运行数据库迁移）或数据库连接错误")
        return 2

    # 3. 测试插入（可选，简单验证表结构）
    try:
        from app.core.database import SessionLocal
        from app.services.retrieval_log_service import RetrievalLogService

        db = SessionLocal()
        try:
            test_log = RetrievalLogService.create_log(
                db=db,
                knowledge_base_id=None,
                user_id=None,
                query="[诊断测试] 可删除",
                chunks_retrieved=0,
                chunks_after_filter=0,
                chunks_after_dedup=0,
                chunks_after_rerank=0,
            )
            db.delete(test_log)
            db.commit()
            print(f"\n3. 插入测试")
            print("   [OK] 表结构正常，可正常写入")
        finally:
            db.close()
    except Exception as e:
        print(f"\n3. 插入测试")
        print(f"   [X] retrieval_log create failed: {e}")
        print("   请检查后端控制台/日志中是否有 retrieval_log create failed 及具体错误")
        return 3

    print("\n" + "=" * 60)
    print("诊断完成。若看板仍无数据，请确认：")
    print("  1. 已完成至少一次 RAG 问答")
    print("  2. 选择「全部知识库」")
    print("  3. 点击看板筛选区右侧的「刷新」按钮")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
