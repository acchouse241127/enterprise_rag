"""
Folder sync service.

Phase 3.2: 文件夹同步（轮询 + 手动）
Author: C2
Date: 2026-02-13
"""

import hashlib
import os
import time
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import FolderSyncConfig, FolderSyncLog, SyncStatus, KnowledgeBase, Document


class FolderSyncService:
    """Service for folder synchronization with knowledge bases."""

    @staticmethod
    def get_config(db: Session, knowledge_base_id: int) -> FolderSyncConfig | None:
        """Get folder sync config for a knowledge base."""
        stmt = select(FolderSyncConfig).where(FolderSyncConfig.knowledge_base_id == knowledge_base_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_or_update_config(
        db: Session,
        knowledge_base_id: int,
        directory_path: str,
        enabled: bool = True,
        sync_interval_minutes: int | None = None,
        file_patterns: str | None = None,
    ) -> tuple[FolderSyncConfig | None, str | None]:
        """Create or update folder sync config."""
        # Verify knowledge base exists
        kb = db.execute(select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)).scalar_one_or_none()
        if kb is None:
            return None, "知识库不存在"

        # Validate directory
        path = Path(directory_path)
        if not path.exists():
            return None, f"目录不存在: {directory_path}"
        if not path.is_dir():
            return None, f"路径不是目录: {directory_path}"

        config = FolderSyncService.get_config(db, knowledge_base_id)
        if config is None:
            config = FolderSyncConfig(
                knowledge_base_id=knowledge_base_id,
                directory_path=str(path.resolve()),
                enabled=enabled,
                sync_interval_minutes=sync_interval_minutes or settings.folder_sync_interval_minutes,
                file_patterns=file_patterns or "*.txt,*.md,*.pdf,*.docx,*.xlsx,*.pptx,*.png,*.jpg,*.jpeg",
            )
            db.add(config)
        else:
            config.directory_path = str(path.resolve())
            config.enabled = enabled
            if sync_interval_minutes is not None:
                config.sync_interval_minutes = sync_interval_minutes
            if file_patterns is not None:
                config.file_patterns = file_patterns
            db.add(config)

        db.commit()
        db.refresh(config)
        return config, None

    @staticmethod
    def delete_config(db: Session, knowledge_base_id: int) -> tuple[bool, str | None]:
        """Delete folder sync config."""
        config = FolderSyncService.get_config(db, knowledge_base_id)
        if config is None:
            return False, "未找到文件夹同步配置"
        db.delete(config)
        db.commit()
        return True, None

    @staticmethod
    def _match_patterns(filename: str, patterns: str) -> bool:
        """Check if filename matches any of the patterns."""
        pattern_list = [p.strip() for p in patterns.split(",") if p.strip()]
        return any(fnmatch(filename.lower(), p.lower()) for p in pattern_list)

    @staticmethod
    def _file_hash(file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def scan_directory(config: FolderSyncConfig) -> list[dict]:
        """
        Scan directory and return list of files with metadata.
        Returns: [{path, filename, mtime, size}, ...]
        """
        directory = Path(config.directory_path)
        if not directory.exists():
            return []

        files = []
        for file_path in directory.rglob("*"):
            if file_path.is_file() and FolderSyncService._match_patterns(file_path.name, config.file_patterns):
                try:
                    stat = file_path.stat()
                    files.append({
                        "path": str(file_path.resolve()),
                        "filename": file_path.name,
                        "relative_path": str(file_path.relative_to(directory)),
                        "mtime": datetime.fromtimestamp(stat.st_mtime),
                        "size": stat.st_size,
                    })
                except Exception:
                    continue
        return files

    @staticmethod
    def sync_folder(
        db: Session,
        knowledge_base_id: int,
        triggered_by: str = "manual",
    ) -> tuple[FolderSyncLog | None, str | None]:
        """
        Synchronize folder with knowledge base.
        
        1. Scan directory for files matching patterns
        2. Compare with existing documents (by filename + path)
        3. Add new files, update changed files (by mtime/hash), mark deleted files
        4. Upload new/changed files via DocumentService
        """
        from app.services.document_service import DocumentService

        config = FolderSyncService.get_config(db, knowledge_base_id)
        if config is None:
            return None, "未配置文件夹同步"

        if not config.enabled:
            return None, "文件夹同步已禁用"

        # Update status to running
        config.last_sync_status = SyncStatus.RUNNING.value
        db.add(config)
        db.commit()

        start_time = time.time()
        files_scanned = 0
        files_added = 0
        files_updated = 0
        files_deleted = 0
        files_failed = 0
        error_messages = []

        try:
            # Scan directory
            scanned_files = FolderSyncService.scan_directory(config)
            files_scanned = len(scanned_files)

            # Get existing documents
            existing_docs = DocumentService.list_by_kb(db, knowledge_base_id)
            existing_map = {}
            for doc in existing_docs:
                if doc.is_current:
                    # Use filename as key (simplified; could use relative_path stored in metadata)
                    existing_map[doc.filename] = doc

            scanned_filenames = {f["filename"] for f in scanned_files}

            # Process each scanned file
            for file_info in scanned_files[:settings.folder_sync_batch_size]:
                filename = file_info["filename"]
                file_path = Path(file_info["path"])

                try:
                    existing_doc = existing_map.get(filename)

                    if existing_doc is None:
                        # New file - upload
                        with open(file_path, "rb") as f:
                            content = f.read()
                        
                        # Create a simple upload-like object
                        class FakeUploadFile:
                            def __init__(self, name, data):
                                self.filename = name
                                self._data = data
                            async def read(self):
                                return self._data

                        fake_file = FakeUploadFile(filename, content)
                        # Use sync wrapper for async upload
                        import asyncio
                        doc, err = asyncio.get_event_loop().run_until_complete(
                            DocumentService.upload(db, knowledge_base_id, fake_file, created_by=None)
                        )
                        if err:
                            files_failed += 1
                            error_messages.append(f"{filename}: {err}")
                        else:
                            files_added += 1
                    else:
                        # Existing file - check if updated
                        file_hash = FolderSyncService._file_hash(file_path)
                        if file_hash != existing_doc.file_hash:
                            # File changed - upload new version
                            with open(file_path, "rb") as f:
                                content = f.read()

                            class FakeUploadFile:
                                def __init__(self, name, data):
                                    self.filename = name
                                    self._data = data
                                async def read(self):
                                    return self._data

                            fake_file = FakeUploadFile(filename, content)
                            import asyncio
                            doc, err = asyncio.get_event_loop().run_until_complete(
                                DocumentService.upload(db, knowledge_base_id, fake_file, created_by=None)
                            )
                            if err:
                                files_failed += 1
                                error_messages.append(f"{filename}: {err}")
                            else:
                                files_updated += 1

                except Exception as e:
                    files_failed += 1
                    error_messages.append(f"{filename}: {str(e)}")

            # Check for deleted files (files in DB but not in directory)
            for filename, doc in existing_map.items():
                if filename not in scanned_filenames:
                    # File deleted from directory - we can optionally mark or delete
                    # For now, just count (don't auto-delete from DB)
                    files_deleted += 1

            # Update config status
            duration = time.time() - start_time
            config.last_sync_at = datetime.now()
            config.last_sync_status = SyncStatus.SUCCESS.value if not error_messages else SyncStatus.FAILED.value
            config.last_sync_message = "; ".join(error_messages[:5]) if error_messages else "同步成功"
            config.last_sync_files_added = files_added
            config.last_sync_files_updated = files_updated
            config.last_sync_files_deleted = files_deleted
            db.add(config)

            # Create log entry
            log = FolderSyncLog(
                folder_sync_config_id=config.id,
                status=config.last_sync_status,
                message=config.last_sync_message,
                files_scanned=files_scanned,
                files_added=files_added,
                files_updated=files_updated,
                files_deleted=files_deleted,
                files_failed=files_failed,
                duration_seconds=duration,
                triggered_by=triggered_by,
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            return log, None

        except Exception as e:
            # Update config with error
            config.last_sync_at = datetime.now()
            config.last_sync_status = SyncStatus.FAILED.value
            config.last_sync_message = str(e)
            db.add(config)
            db.commit()
            return None, str(e)

    @staticmethod
    def get_sync_logs(
        db: Session,
        knowledge_base_id: int,
        limit: int = 20,
    ) -> list[FolderSyncLog]:
        """Get sync logs for a knowledge base."""
        config = FolderSyncService.get_config(db, knowledge_base_id)
        if config is None:
            return []

        stmt = (
            select(FolderSyncLog)
            .where(FolderSyncLog.folder_sync_config_id == config.id)
            .order_by(FolderSyncLog.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_all_enabled_configs(db: Session) -> list[FolderSyncConfig]:
        """Get all enabled folder sync configs (for background polling)."""
        stmt = select(FolderSyncConfig).where(FolderSyncConfig.enabled.is_(True))
        return list(db.execute(stmt).scalars().all())
