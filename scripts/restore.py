#!/usr/bin/env python3
"""
数据恢复脚本

恢复内容：
1. PostgreSQL 数据库
2. ChromaDB 向量数据
3. 上传的文件

用法：
    python scripts/restore.py /path/to/backup [--confirm]

Author: C2
Date: 2026-02-21
"""

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def confirm_restore() -> bool:
    """确认恢复操作"""
    print("\n" + "=" * 50)
    print("警告：恢复操作将覆盖现有数据！")
    print("=" * 50)
    response = input("确认继续？请输入 'yes' 继续: ")
    return response.strip().lower() == "yes"


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    print(f"执行: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def restore_postgres(backup_dir: Path, pg_env: dict) -> bool:
    """恢复 PostgreSQL 数据库"""
    print("\n=== 恢复 PostgreSQL ===")

    backup_file = backup_dir / "postgres_dump.sql.gz"
    if not backup_file.exists():
        print(f"备份文件不存在: {backup_file}")
        return False

    # 解压缩
    with gzip.open(backup_file, "rb") as f:
        sql_content = f.read()

    env = os.environ.copy()
    env["PGPASSWORD"] = pg_env.get("POSTGRES_PASSWORD", "enterprise_rag")

    # 恢复数据库
    cmd = [
        "psql",
        "-h", pg_env.get("POSTGRES_HOST", "localhost"),
        "-p", str(pg_env.get("POSTGRES_PORT", 5432)),
        "-U", pg_env.get("POSTGRES_USER", "enterprise_rag"),
        "-d", pg_env.get("POSTGRES_DB", "enterprise_rag"),
    ]

    print(f"执行: {' '.join(cmd)} < {backup_file}")
    result = subprocess.run(cmd, env=env, input=sql_content, capture_output=True)

    if result.returncode != 0:
        print(f"psql 警告/错误: {result.stderr.decode()}")
        # psql 可能返回警告但仍成功，不抛出异常

    print("PostgreSQL 恢复完成")
    return True


def restore_chroma(backup_dir: Path, chroma_data_dir: Path) -> bool:
    """恢复 ChromaDB 向量数据"""
    print("\n=== 恢复 ChromaDB ===")

    backup_file = backup_dir / "chroma_backup.tar.gz"
    if not backup_file.exists():
        print(f"备份文件不存在: {backup_file}")
        return False

    # 备份现有数据
    if chroma_data_dir.exists():
        backup_existing = chroma_data_dir.with_suffix(".bak")
        if backup_existing.exists():
            shutil.rmtree(backup_existing)
        shutil.move(str(chroma_data_dir), str(backup_existing))
        print(f"现有数据已备份到: {backup_existing}")

    # 解压恢复
    cmd = [
        "tar",
        "-xzf",
        str(backup_file),
        "-C",
        str(chroma_data_dir.parent),
    ]

    run_command(cmd)
    print("ChromaDB 恢复完成")
    return True


def restore_uploads(backup_dir: Path, uploads_dir: Path) -> bool:
    """恢复上传的文件"""
    print("\n=== 恢复上传文件 ===")

    backup_file = backup_dir / "uploads_backup.tar.gz"
    if not backup_file.exists():
        print(f"备份文件不存在: {backup_file}")
        return False

    # 备份现有数据
    if uploads_dir.exists():
        backup_existing = uploads_dir.with_suffix(".bak")
        if backup_existing.exists():
            shutil.rmtree(backup_existing)
        shutil.move(str(uploads_dir), str(backup_existing))
        print(f"现有数据已备份到: {backup_existing}")

    # 解压恢复
    cmd = [
        "tar",
        "-xzf",
        str(backup_file),
        "-C",
        str(uploads_dir.parent),
    ]

    run_command(cmd)
    print("上传文件恢复完成")
    return True


def main():
    parser = argparse.ArgumentParser(description="Enterprise RAG 数据恢复")
    parser.add_argument(
        "backup_dir",
        type=str,
        help="备份目录路径",
    )
    parser.add_argument(
        "--confirm",
        "-y",
        action="store_true",
        help="跳过确认直接恢复",
    )
    parser.add_argument(
        "--postgres-only",
        action="store_true",
        help="仅恢复 PostgreSQL",
    )
    parser.add_argument(
        "--chroma-only",
        action="store_true",
        help="仅恢复 ChromaDB",
    )
    parser.add_argument(
        "--uploads-only",
        action="store_true",
        help="仅恢复上传文件",
    )
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir)
    if not backup_dir.exists():
        print(f"错误：备份目录不存在: {backup_dir}")
        sys.exit(1)

    # 检查清单
    manifest_file = backup_dir / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"备份时间: {manifest.get('timestamp', '未知')}")
        print(f"备份内容: {[b['type'] for b in manifest.get('backups', [])]}")

    # 确认
    if not args.confirm and not confirm_restore():
        print("取消恢复")
        sys.exit(0)

    # 从环境变量读取配置
    pg_env = {
        "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "POSTGRES_PORT": int(os.environ.get("POSTGRES_PORT", 5432)),
        "POSTGRES_USER": os.environ.get("POSTGRES_USER", "enterprise_rag"),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", "enterprise_rag"),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB", "enterprise_rag"),
    }

    # 数据目录
    data_dir = PROJECT_ROOT / "data"
    chroma_data_dir = data_dir / "vectors"
    uploads_dir = data_dir / "uploads"

    print(f"\n开始恢复: {backup_dir}")

    try:
        success = True

        if not args.chroma_only and not args.uploads_only:
            if not restore_postgres(backup_dir, pg_env):
                success = False

        if not args.postgres_only and not args.uploads_only:
            if not restore_chroma(backup_dir, chroma_data_dir):
                success = False

        if not args.postgres_only and not args.chroma_only:
            if not restore_uploads(backup_dir, uploads_dir):
                success = False

        if success:
            print("\n=== 恢复完成 ===")
            print("建议重启所有服务以确保数据一致性")
        else:
            print("\n=== 恢复部分失败 ===")
            sys.exit(1)

    except Exception as e:
        print(f"\n恢复失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
