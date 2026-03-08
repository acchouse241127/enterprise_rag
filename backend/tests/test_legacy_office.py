"""
Unit tests for legacy Office format conversion.

Tests for app/document_parser/legacy_office.py
Author: C2
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestFindSoffice:
    """Tests for _find_soffice function."""

    def test_find_soffice_from_path(self):
        """Test finding soffice from PATH."""
        from app.document_parser.legacy_office import _find_soffice

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/soffice"
            result = _find_soffice()
            assert result == "/usr/bin/soffice"

    def test_find_soffice_libreoffice_alias(self):
        """Test finding libreoffice command."""
        from app.document_parser.legacy_office import _find_soffice

        with patch("shutil.which") as mock_which:
            # First call for "soffice" returns None, second for "libreoffice" succeeds
            mock_which.side_effect = [None, "/usr/bin/libreoffice"]
            result = _find_soffice()
            assert result == "/usr/bin/libreoffice"

    def test_find_soffice_windows_common_path(self):
        """Test finding soffice from Windows common path."""
        from app.document_parser.legacy_office import _find_soffice

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch.object(Path, "exists") as mock_exists:
                mock_exists.return_value = True
                result = _find_soffice()
                # Should find the Windows path
                assert result is not None
                assert "soffice.exe" in result

    def test_find_soffice_not_found(self):
        """Test when soffice is not found anywhere."""
        from app.document_parser.legacy_office import _find_soffice

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch.object(Path, "exists") as mock_exists:
                mock_exists.return_value = False
                result = _find_soffice()
                assert result is None


class TestConvertDocToDocx:
    """Tests for convert_doc_to_docx function."""

    def test_convert_doc_to_docx_success(self):
        """Test successful .doc to .docx conversion."""
        from app.document_parser.legacy_office import convert_doc_to_docx

        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with patch("app.document_parser.legacy_office._convert") as mock_convert:
                expected_path = Path("/tmp/converted.docx")
                mock_convert.return_value = expected_path
                result = convert_doc_to_docx(tmp_path)
                mock_convert.assert_called_once_with(tmp_path, "docx")
                assert result == expected_path
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_convert_doc_to_docx_passes_correct_extension(self):
        """Test that convert_doc_to_docx passes 'docx' as target extension."""
        from app.document_parser.legacy_office import convert_doc_to_docx

        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with patch("app.document_parser.legacy_office._convert") as mock_convert:
                mock_convert.return_value = Path("/tmp/output.docx")
                convert_doc_to_docx(tmp_path)
                args = mock_convert.call_args
                assert args[0][1] == "docx"
        finally:
            tmp_path.unlink(missing_ok=True)


class TestConvertPptToPptx:
    """Tests for convert_ppt_to_pptx function."""

    def test_convert_ppt_to_pptx_success(self):
        """Test successful .ppt to .pptx conversion."""
        from app.document_parser.legacy_office import convert_ppt_to_pptx

        with tempfile.NamedTemporaryFile(suffix=".ppt", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with patch("app.document_parser.legacy_office._convert") as mock_convert:
                expected_path = Path("/tmp/converted.pptx")
                mock_convert.return_value = expected_path
                result = convert_ppt_to_pptx(tmp_path)
                mock_convert.assert_called_once_with(tmp_path, "pptx")
                assert result == expected_path
        finally:
            tmp_path.unlink(missing_ok=True)


class TestConvert:
    """Tests for _convert internal function."""

    def test_convert_no_soffice_raises_runtime_error(self):
        """Test that missing soffice raises RuntimeError."""
        from app.document_parser.legacy_office import _convert

        with patch("app.document_parser.legacy_office._find_soffice") as mock_find:
            mock_find.return_value = None
            with pytest.raises(RuntimeError) as exc_info:
                _convert(Path("/tmp/test.doc"), "docx")
            assert "LibreOffice" in str(exc_info.value)

    def test_convert_file_not_found_raises_error(self):
        """Test that non-existent file raises FileNotFoundError."""
        from app.document_parser.legacy_office import _convert

        with patch("app.document_parser.legacy_office._find_soffice") as mock_find:
            mock_find.return_value = "/usr/bin/soffice"
            with patch.object(Path, "exists") as mock_exists:
                mock_exists.return_value = False
                with pytest.raises(FileNotFoundError):
                    _convert(Path("/nonexistent/file.doc"), "docx")

    def test_convert_timeout_raises_runtime_error(self):
        """Test that conversion timeout raises RuntimeError."""
        from app.document_parser.legacy_office import _convert
        import subprocess

        with patch("app.document_parser.legacy_office._find_soffice") as mock_find:
            mock_find.return_value = "/usr/bin/soffice"
            with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                with patch.object(Path, "exists") as mock_exists:
                    mock_exists.return_value = True
                    with patch("subprocess.run") as mock_run:
                        mock_run.side_effect = subprocess.TimeoutExpired(cmd="soffice", timeout=120)
                        with pytest.raises(RuntimeError) as exc_info:
                            _convert(tmp_path, "docx")
                        assert "超时" in str(exc_info.value)
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_convert_process_error_raises_runtime_error(self):
        """Test that conversion process error raises RuntimeError."""
        from app.document_parser.legacy_office import _convert
        import subprocess

        with patch("app.document_parser.legacy_office._find_soffice") as mock_find:
            mock_find.return_value = "/usr/bin/soffice"
            with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                with patch.object(Path, "exists") as mock_exists:
                    mock_exists.return_value = True
                    with patch("subprocess.run") as mock_run:
                        mock_run.side_effect = subprocess.CalledProcessError(
                            returncode=1, cmd="soffice", stderr="Conversion failed"
                        )
                        with pytest.raises(RuntimeError) as exc_info:
                            _convert(tmp_path, "docx")
                        assert "失败" in str(exc_info.value)
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_convert_output_not_generated_raises_runtime_error(self):
        """Test that missing output file raises RuntimeError."""
        from app.document_parser.legacy_office import _convert

        with patch("app.document_parser.legacy_office._find_soffice") as mock_find:
            mock_find.return_value = "/usr/bin/soffice"
            with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                with patch.object(Path, "exists") as mock_exists:
                    # First call for input file check, second for output file check
                    mock_exists.side_effect = [True, False]
                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)
                        with patch("tempfile.TemporaryDirectory"):
                            with patch("pathlib.Path.resolve") as mock_resolve:
                                mock_resolve.return_value = tmp_path
                                with pytest.raises(RuntimeError) as exc_info:
                                    _convert(tmp_path, "docx")
                                assert "未生成" in str(exc_info.value)
            finally:
                tmp_path.unlink(missing_ok=True)


class TestConvertIntegration:
    """Integration tests that require LibreOffice installed."""

    @pytest.mark.skip(reason="Requires LibreOffice installation")
    def test_real_doc_conversion(self):
        """Test real .doc file conversion (requires LibreOffice)."""
        # This test is skipped by default as it requires:
        # 1. LibreOffice to be installed
        # 2. A real .doc test file
        pass
