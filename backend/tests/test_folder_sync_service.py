"""
Unit tests for FolderSyncService.

Tests for app/services/folder_sync_service.py
Author: C2
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock


class TestFolderSyncServiceConfig:
    """Tests for FolderSyncService config operations."""

    def test_get_config_found(self):
        """Test getting existing config."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_config = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        result = FolderSyncService.get_config(mock_db, 1)
        assert result == mock_config

    def test_get_config_not_found(self):
        """Test getting non-existent config."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = FolderSyncService.get_config(mock_db, 999)
        assert result is None

    def test_create_config_kb_not_found(self):
        """Test creating config when KB doesn't exist."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_kb_result

        with tempfile.TemporaryDirectory() as tmpdir:
            result, err = FolderSyncService.create_or_update_config(
                mock_db, 1, tmpdir
            )
            assert result is None
            assert "知识库不存在" in err

    def test_create_config_directory_not_exists(self):
        """Test creating config when directory doesn't exist."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_kb_result

        result, err = FolderSyncService.create_or_update_config(
            mock_db, 1, "/nonexistent/directory"
        )
        assert result is None
        assert "目录不存在" in err

    def test_create_config_path_is_file(self):
        """Test creating config when path is a file."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_kb_result

        with tempfile.NamedTemporaryFile() as tmpfile:
            result, err = FolderSyncService.create_or_update_config(
                mock_db, 1, tmpfile.name
            )
            assert result is None
            assert "路径不是目录" in err

    def test_create_config_success(self):
        """Test creating new config successfully."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_kb_result

        with patch.object(FolderSyncService, "get_config", return_value=None):
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch("app.services.folder_sync_service.FolderSyncConfig") as MockConfig:
                    mock_config = MagicMock()
                    MockConfig.return_value = mock_config

                    result, err = FolderSyncService.create_or_update_config(
                        mock_db, 1, tmpdir
                    )
                    assert result == mock_config
                    assert err is None
                    mock_db.add.assert_called()
                    mock_db.commit.assert_called()

    def test_update_config_success(self):
        """Test updating existing config."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_config = MagicMock()

        with patch.object(FolderSyncService, "get_config", return_value=mock_config):
            with tempfile.TemporaryDirectory() as tmpdir:
                result, err = FolderSyncService.create_or_update_config(
                    mock_db, 1, tmpdir, enabled=True, sync_interval_minutes=30
                )
                assert result == mock_config
                assert err is None
                mock_db.add.assert_called()

    def test_delete_config_found(self):
        """Test deleting existing config."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_config = MagicMock()

        with patch.object(FolderSyncService, "get_config", return_value=mock_config):
            success, err = FolderSyncService.delete_config(mock_db, 1)
            assert success == True
            assert err is None
            mock_db.delete.assert_called()

    def test_delete_config_not_found(self):
        """Test deleting non-existent config."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()

        with patch.object(FolderSyncService, "get_config", return_value=None):
            success, err = FolderSyncService.delete_config(mock_db, 999)
            assert success == False
            assert "未找到" in err


class TestFolderSyncServicePatterns:
    """Tests for pattern matching."""

    def test_match_patterns_exact_match(self):
        """Test pattern matching with exact match."""
        from app.services.folder_sync_service import FolderSyncService

        assert FolderSyncService._match_patterns("test.txt", "*.txt") == True
        assert FolderSyncService._match_patterns("test.pdf", "*.pdf") == True

    def test_match_patterns_no_match(self):
        """Test pattern matching with no match."""
        from app.services.folder_sync_service import FolderSyncService

        assert FolderSyncService._match_patterns("test.txt", "*.pdf") == False
        assert FolderSyncService._match_patterns("test.doc", "*.txt,*.pdf") == False

    def test_match_patterns_multiple_patterns(self):
        """Test pattern matching with multiple patterns."""
        from app.services.folder_sync_service import FolderSyncService

        assert FolderSyncService._match_patterns("test.txt", "*.txt,*.pdf,*.doc") == True
        assert FolderSyncService._match_patterns("test.pdf", "*.txt,*.pdf,*.doc") == True
        assert FolderSyncService._match_patterns("test.xlsx", "*.txt,*.pdf,*.doc") == False

    def test_match_patterns_case_insensitive(self):
        """Test pattern matching is case insensitive."""
        from app.services.folder_sync_service import FolderSyncService

        assert FolderSyncService._match_patterns("TEST.TXT", "*.txt") == True
        assert FolderSyncService._match_patterns("Test.PDF", "*.pdf") == True

    def test_match_patterns_with_spaces(self):
        """Test pattern matching handles spaces in pattern list."""
        from app.services.folder_sync_service import FolderSyncService

        assert FolderSyncService._match_patterns("test.txt", "*.txt, *.pdf") == True
        assert FolderSyncService._match_patterns("test.pdf", "  *.pdf  , *.txt") == True

    def test_match_patterns_empty_patterns(self):
        """Test pattern matching with empty pattern string."""
        from app.services.folder_sync_service import FolderSyncService

        assert FolderSyncService._match_patterns("test.txt", "") == False
        assert FolderSyncService._match_patterns("test.txt", "   ") == False


class TestFolderSyncServiceFileHash:
    """Tests for file hash calculation."""

    def test_file_hash_consistent(self):
        """Test file hash is consistent."""
        from app.services.folder_sync_service import FolderSyncService

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)

        try:
            hash1 = FolderSyncService._file_hash(tmp_path)
            hash2 = FolderSyncService._file_hash(tmp_path)
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
        finally:
            tmp_path.unlink()

    def test_file_hash_different_content(self):
        """Test file hash differs for different content."""
        from app.services.folder_sync_service import FolderSyncService

        with tempfile.NamedTemporaryFile(delete=False) as tmp1:
            tmp1.write(b"content 1")
            path1 = Path(tmp1.name)

        with tempfile.NamedTemporaryFile(delete=False) as tmp2:
            tmp2.write(b"content 2")
            path2 = Path(tmp2.name)

        try:
            hash1 = FolderSyncService._file_hash(path1)
            hash2 = FolderSyncService._file_hash(path2)
            assert hash1 != hash2
        finally:
            path1.unlink()
            path2.unlink()

    def test_file_hash_large_file(self):
        """Test file hash for larger file (tests chunked reading)."""
        from app.services.folder_sync_service import FolderSyncService

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write more than 8192 bytes to test chunking
            tmp.write(b"x" * 10000)
            tmp_path = Path(tmp.name)

        try:
            file_hash = FolderSyncService._file_hash(tmp_path)
            assert len(file_hash) == 64
        finally:
            tmp_path.unlink()


class TestFolderSyncServiceScanDirectory:
    """Tests for directory scanning."""

    def test_scan_directory_empty(self):
        """Test scanning empty directory."""
        from app.services.folder_sync_service import FolderSyncService

        mock_config = MagicMock()
        mock_config.directory_path = tempfile.mkdtemp()
        mock_config.file_patterns = "*.txt"

        try:
            files = FolderSyncService.scan_directory(mock_config)
            assert files == []
        finally:
            os.rmdir(mock_config.directory_path)

    def test_scan_directory_nonexistent(self):
        """Test scanning non-existent directory."""
        from app.services.folder_sync_service import FolderSyncService

        mock_config = MagicMock()
        mock_config.directory_path = "/nonexistent/directory"
        mock_config.file_patterns = "*.txt"

        files = FolderSyncService.scan_directory(mock_config)
        assert files == []

    def test_scan_directory_with_files(self):
        """Test scanning directory with matching files."""
        from app.services.folder_sync_service import FolderSyncService

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "test1.txt").write_text("content 1")
            Path(tmpdir, "test2.txt").write_text("content 2")

            mock_config = MagicMock()
            mock_config.directory_path = tmpdir
            mock_config.file_patterns = "*.txt"

            files = FolderSyncService.scan_directory(mock_config)
            assert len(files) == 2
            filenames = [f["filename"] for f in files]
            assert "test1.txt" in filenames
            assert "test2.txt" in filenames

    def test_scan_directory_filters_by_pattern(self):
        """Test scanning filters by file pattern."""
        from app.services.folder_sync_service import FolderSyncService

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text("text")
            Path(tmpdir, "test.pdf").write_text("pdf")
            Path(tmpdir, "test.doc").write_text("doc")

            mock_config = MagicMock()
            mock_config.directory_path = tmpdir
            mock_config.file_patterns = "*.txt,*.pdf"

            files = FolderSyncService.scan_directory(mock_config)
            assert len(files) == 2
            filenames = [f["filename"] for f in files]
            assert "test.txt" in filenames
            assert "test.pdf" in filenames
            assert "test.doc" not in filenames

    def test_scan_directory_includes_metadata(self):
        """Test scanning includes file metadata."""
        from app.services.folder_sync_service import FolderSyncService

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "test.txt")
            test_file.write_text("content")

            mock_config = MagicMock()
            mock_config.directory_path = tmpdir
            mock_config.file_patterns = "*.txt"

            files = FolderSyncService.scan_directory(mock_config)
            assert len(files) == 1
            assert "path" in files[0]
            assert "filename" in files[0]
            assert "relative_path" in files[0]
            assert "mtime" in files[0]
            assert "size" in files[0]

    def test_scan_directory_recursive(self):
        """Test scanning includes files in subdirectories."""
        from app.services.folder_sync_service import FolderSyncService

        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(tmpdir, "root.txt").write_text("root")
            Path(subdir, "nested.txt").write_text("nested")

            mock_config = MagicMock()
            mock_config.directory_path = tmpdir
            mock_config.file_patterns = "*.txt"

            files = FolderSyncService.scan_directory(mock_config)
            assert len(files) == 2


class TestFolderSyncServiceGetLogs:
    """Tests for getting sync logs."""

    def test_get_sync_logs_no_config(self):
        """Test getting logs when no config exists."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()

        with patch.object(FolderSyncService, "get_config", return_value=None):
            logs = FolderSyncService.get_sync_logs(mock_db, 1)
            assert logs == []

    def test_get_sync_logs_with_config(self):
        """Test getting logs with config."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.id = 1

        mock_result = MagicMock()
        mock_logs = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db.execute.return_value = mock_result

        with patch.object(FolderSyncService, "get_config", return_value=mock_config):
            logs = FolderSyncService.get_sync_logs(mock_db, 1)
            assert len(logs) == 2


class TestFolderSyncServiceGetAllEnabled:
    """Tests for getting all enabled configs."""

    def test_get_all_enabled_configs(self):
        """Test getting all enabled configs."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_configs = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_configs
        mock_db.execute.return_value = mock_result

        configs = FolderSyncService.get_all_enabled_configs(mock_db)
        assert len(configs) == 2


class TestFolderSyncServiceSyncFolder:
    """Tests for sync_folder method."""

    def test_sync_folder_no_config(self):
        """Test sync when no config exists."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()

        with patch.object(FolderSyncService, "get_config", return_value=None):
            result, err = FolderSyncService.sync_folder(mock_db, 1)
            assert result is None
            assert "未配置" in err

    def test_sync_folder_disabled(self):
        """Test sync when config is disabled."""
        from app.services.folder_sync_service import FolderSyncService

        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.enabled = False

        with patch.object(FolderSyncService, "get_config", return_value=mock_config):
            result, err = FolderSyncService.sync_folder(mock_db, 1)
            assert result is None
            assert "禁用" in err
