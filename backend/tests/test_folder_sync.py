"""
Tests for folder sync service and APIs.

Phase 3.2: 文件夹同步测试
Author: C2
Date: 2026-02-13
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models import FolderSyncConfig, SyncStatus


class TestFolderSyncConfig:
    """Test FolderSyncConfig model."""

    def test_sync_status_enum(self):
        """Test SyncStatus enum values."""
        assert SyncStatus.IDLE.value == "idle"
        assert SyncStatus.RUNNING.value == "running"
        assert SyncStatus.SUCCESS.value == "success"
        assert SyncStatus.FAILED.value == "failed"


class TestFolderSyncService:
    """Test FolderSyncService."""

    def test_match_patterns(self):
        """Test file pattern matching."""
        from app.services.folder_sync_service import FolderSyncService

        # Test matching
        assert FolderSyncService._match_patterns("test.txt", "*.txt")
        assert FolderSyncService._match_patterns("test.PDF", "*.pdf")  # case insensitive
        assert FolderSyncService._match_patterns("doc.docx", "*.txt,*.md,*.docx")
        
        # Test non-matching
        assert not FolderSyncService._match_patterns("test.jpg", "*.txt,*.pdf")

    def test_file_hash(self):
        """Test file hash calculation."""
        from app.services.folder_sync_service import FolderSyncService

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            hash1 = FolderSyncService._file_hash(Path(temp_path))
            hash2 = FolderSyncService._file_hash(Path(temp_path))
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_scan_directory(self):
        """Test directory scanning."""
        from app.services.folder_sync_service import FolderSyncService

        # Create temp directory with files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test1.txt").write_text("content1")
            (Path(tmpdir) / "test2.md").write_text("content2")
            (Path(tmpdir) / "test3.jpg").write_text("image")  # Should not match
            
            # Create mock config
            config = MagicMock()
            config.directory_path = tmpdir
            config.file_patterns = "*.txt,*.md"

            files = FolderSyncService.scan_directory(config)
            
            assert len(files) == 2
            filenames = {f["filename"] for f in files}
            assert "test1.txt" in filenames
            assert "test2.md" in filenames
            assert "test3.jpg" not in filenames


class TestRetrievalLogService:
    """Test RetrievalLogService."""

    def test_feedback_type_enum(self):
        """Test FeedbackType enum values."""
        from app.models import FeedbackType

        assert FeedbackType.HELPFUL.value == "helpful"
        assert FeedbackType.NOT_HELPFUL.value == "not_helpful"


class TestRetrievalLogModel:
    """Test RetrievalLog and RetrievalFeedback models."""

    def test_retrieval_log_fields(self):
        """Test RetrievalLog has expected fields."""
        from app.models import RetrievalLog

        # Check model has key fields
        assert hasattr(RetrievalLog, "id")
        assert hasattr(RetrievalLog, "knowledge_base_id")
        assert hasattr(RetrievalLog, "query")
        assert hasattr(RetrievalLog, "chunks_retrieved")
        assert hasattr(RetrievalLog, "top_chunk_score")
        assert hasattr(RetrievalLog, "chunk_details")
        assert hasattr(RetrievalLog, "created_at")

    def test_retrieval_feedback_fields(self):
        """Test RetrievalFeedback has expected fields."""
        from app.models import RetrievalFeedback

        assert hasattr(RetrievalFeedback, "id")
        assert hasattr(RetrievalFeedback, "retrieval_log_id")
        assert hasattr(RetrievalFeedback, "feedback_type")
        assert hasattr(RetrievalFeedback, "is_sample_marked")
        assert hasattr(RetrievalFeedback, "comment")


class TestPhase32Config:
    """Test Phase 3.2 configuration."""

    def test_folder_sync_config_defaults(self):
        """Test folder sync config defaults."""
        from app.config import settings

        assert hasattr(settings, "folder_sync_enabled")
        assert hasattr(settings, "folder_sync_interval_minutes")
        assert hasattr(settings, "folder_sync_batch_size")
        assert settings.folder_sync_interval_minutes >= 5

    def test_retrieval_log_config_defaults(self):
        """Test retrieval log config defaults."""
        from app.config import settings

        assert hasattr(settings, "retrieval_log_enabled")
        assert hasattr(settings, "retrieval_log_max_chunks")
        assert settings.retrieval_log_max_chunks >= 1
