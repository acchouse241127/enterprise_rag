#!/usr/bin/env python3
"""
数据备份脚本

备份内容：
1. PostgreSQL 数据库
2. ChromaDB 向量数据
3. 上传的文件

用法：
    python scripts/backup.py [--output-dir /path/to/backup]

Author: C2
Date: 2026-02-21
"""

import argparse
import gzip
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    print(f"执行: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def backup_postgres(output_dir: Path, pg_env: dict) -> Path:
    """备份 PostgreSQL 数据库"""
    print("\n=== 备份 PostgreSQL ===")

    backup_file = output_dir / "postgres_dump.sql.gz"

    # 使用 pg_dump 导出
    cmd = [
        "pg_dump",
        "-h", pg_env.get("POSTGRES_HOST", "localhost"),
        "-p", str(pg_env.get("POSTGRES_PORT", 5432)),
        "-U", pg_env.get("POSTGRES_USER", "enterprise_rag"),
        "-d", pg_env.get("POSTGRES_DB", "enterprise_rag"),
        "--no-owner",
        "--no-acl",
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = pg_env.get("POSTGRES_PASSWORD", "enterprise_rag")

    print(f"执行: {' '.join(cmd)} > {backup_file}")
    result = subprocess.run(cmd, env=env, capture_output=True)

    if result.returncode != 0:
        print(f"pg_dump 错误: {result.stderr.decode()}")
        raise RuntimeError("PostgreSQL 备份失败")

    # 压缩
    with open(backup_file, "wb") as f:
        f.write(gzip.compress(result.stdout))

    print(f"PostgreSQL 备份完成: {backup_file}")
    return backup_file


def backup_chroma(output_dir: Path, chroma_data_dir: Path) -> Path | None:
    """备份 ChromaDB 向量数据"""
    print("\n=== 备份 ChromaDB ===")

    if not chroma_data_dir.exists():
        print(f"ChromaDB 数据目录不存在: {chroma_data_dir}")
        return None

    backup_file = output_dir / "chroma_backup.tar.gz"

    # 打包 ChromaDB 数据目录
    cmd = [
        "tar",
        "-czf",
        str(backup_file),
        "-C",
        str(chroma_data_dir.parent),
        chroma_data_dir.name,
    ]

    run_command(cmd)
    print(f"ChromaDB 备份完成: {backup_file}")
    return backup_file


def backup_uploads(output_dir: Path, uploads_dir: Path) -> Path | None:
    """备份上传的文件"""
    print("\n=== 备份上传文件 ===")

    if not uploads_dir.exists():
        print(f"上传目录不存在: {uploads_dir}")
        return None

    backup_file = output_dir / "uploads_backup.tar.gz"

    cmd = [
        "tar",
        "-czf",
        str(backup_file),
        "-C",
        str(uploads_dir.parent),
        uploads_dir.name,
    ]

    run_command(cmd)
    print(f"上传文件备份完成: {backup_file}")
    return backup_file


def main():
    parser = argparse.ArgumentParser(description="Enterprise RAG 数据备份")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=None,
        help="备份输出目录（默认: ./backups/YYYYMMDD_HHMMSS）",
    )
    args = parser.parse_args()

    # 从环境变量或 .env 读取配置
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

    # 输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = PROJECT_ROOT / "backups" / timestamp

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"备份目录: {output_dir}")
    print(f"开始备份: {datetime.now().isoformat()}")

    manifest = {
        "timestamp": datetime.now().isoformat(),
        "backups": [],
    }

    # 执行备份
    try:
        pg_backup = backup_postgres(output_dir, pg_env)
        manifest["backups"].append({"type": "postgres", "file": pg_backup.name})

        chroma_backup = backup_chroma(output_dir, chroma_data_dir)
        if chroma_backup:
            manifest["backups"].append({"type": "chroma", "file": chroma_backup.name})

        uploads_backup = backup_uploads(output_dir, uploads_dir)
        if uploads_backup:
            manifest["backups"].append({"type": "uploads", "file": uploads_backup.name})

        # 写入清单
        import json
        manifest_file = output_dir / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"\n=== 备份完成 ===")
        print(f"备份目录: {output_dir}")
        print(f"完成时间: {datetime.now().isoformat()}")

        # 计算总大小
        total_size = sum(f.stat().st_size for f in output_dir.iterdir() if f.is_file())
        print(f"总大小: {total_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"\n备份失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
