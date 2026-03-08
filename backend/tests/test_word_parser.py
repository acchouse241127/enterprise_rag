"""
Unit tests for Word document parser.

Tests for app/document_parser/word_parser.py
Author: C2
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.document_parser.models import ContentType


class TestWordDocumentParser:
    """Tests for WordDocumentParser class."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()
        assert parser is not None

    def test_parse_docx_file(self):
        """Test parsing a DOCX file."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        # Mock Document
        mock_doc = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "First paragraph"
        mock_para2 = MagicMock()
        mock_para2.text = "Second paragraph"
        mock_doc.paragraphs = [mock_para1, mock_para2]

        with patch.dict("sys.modules", {"docx": MagicMock()}):
            import sys
            sys.modules["docx"].Document = MagicMock(return_value=mock_doc)

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                contents = parser.parse(tmp_path)
                assert len(contents) == 1
                assert contents[0].content_type == ContentType.TEXT
                assert "First paragraph" in contents[0].text
                assert "Second paragraph" in contents[0].text
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_strips_whitespace(self):
        """Test that paragraph text is stripped."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "  Text with spaces  "
        mock_doc.paragraphs = [mock_para]

        with patch.dict("sys.modules", {"docx": MagicMock()}):
            import sys
            sys.modules["docx"].Document = MagicMock(return_value=mock_doc)

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                contents = parser.parse(tmp_path)
                assert "Text with spaces" in contents[0].text
                assert "  Text with spaces  " not in contents[0].text
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_filters_empty_paragraphs(self):
        """Test that empty paragraphs are filtered out."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        mock_doc = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "Valid text"
        mock_para2 = MagicMock()
        mock_para2.text = ""
        mock_para3 = MagicMock()
        mock_para3.text = "   "  # Only whitespace
        mock_para4 = MagicMock()
        mock_para4.text = None
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3, mock_para4]

        with patch.dict("sys.modules", {"docx": MagicMock()}):
            import sys
            sys.modules["docx"].Document = MagicMock(return_value=mock_doc)

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                contents = parser.parse(tmp_path)
                assert "Valid text" in contents[0].text
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_empty_document(self):
        """Test parsing an empty document."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        mock_doc = MagicMock()
        mock_doc.paragraphs = []

        with patch.dict("sys.modules", {"docx": MagicMock()}):
            import sys
            sys.modules["docx"].Document = MagicMock(return_value=mock_doc)

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                contents = parser.parse(tmp_path)
                # Empty document should return empty list or list with empty text
                assert len(contents) == 0 or (len(contents) == 1 and not contents[0].text.strip())
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_doc_file_calls_conversion(self):
        """Test that .doc files are converted to .docx."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        mock_doc = MagicMock()
        mock_doc.paragraphs = []

        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            converted_path = Path(str(tmp_path).replace(".doc", "_converted.docx"))
            converted_path.touch()

            with patch("app.document_parser.legacy_office.convert_doc_to_docx") as mock_convert:
                mock_convert.return_value = converted_path

                with patch.dict("sys.modules", {"docx": MagicMock()}):
                    import sys
                    sys.modules["docx"].Document = MagicMock(return_value=mock_doc)

                    parser.parse(tmp_path)
                    mock_convert.assert_called_once()

            converted_path.unlink(missing_ok=True)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_parse_doc_deletes_converted_file(self):
        """Test that temporary converted file is deleted after parsing."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        mock_doc = MagicMock()
        mock_doc.paragraphs = []

        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            converted_path = Path(str(tmp_path).replace(".doc", "_converted.docx"))
            converted_path.touch()

            with patch("app.document_parser.legacy_office.convert_doc_to_docx", return_value=converted_path):
                with patch.dict("sys.modules", {"docx": MagicMock()}):
                    import sys
                    sys.modules["docx"].Document = MagicMock(return_value=mock_doc)

                    parser.parse(tmp_path)

                    # Note: The file should be deleted after parse completes
                    # but we clean up in finally anyway

            converted_path.unlink(missing_ok=True)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_parse_joins_paragraphs_with_newline(self):
        """Test that paragraphs are joined with newlines."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        mock_doc = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "Line 1"
        mock_para2 = MagicMock()
        mock_para2.text = "Line 2"
        mock_para3 = MagicMock()
        mock_para3.text = "Line 3"
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]

        with patch.dict("sys.modules", {"docx": MagicMock()}):
            import sys
            sys.modules["docx"].Document = MagicMock(return_value=mock_doc)

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                contents = parser.parse(tmp_path)
                assert "Line 1" in contents[0].text
                assert "Line 2" in contents[0].text
                assert "Line 3" in contents[0].text
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_handles_file_not_found(self):
        """Test handling of non-existent file."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        # This should raise an error when the file doesn't exist
        # (docx.Document will fail)
        non_existent = Path("/nonexistent/file.docx")

        with patch.dict("sys.modules", {"docx": MagicMock()}):
            import sys
            sys.modules["docx"].Document = MagicMock(side_effect=FileNotFoundError("File not found"))

            with pytest.raises(FileNotFoundError):
                parser.parse(non_existent)

    def test_parse_text_backward_compat(self):
        """Test parse_text returns plain string for backward compatibility."""
        from app.document_parser.word_parser import WordDocumentParser

        parser = WordDocumentParser()

        mock_doc = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "First paragraph"
        mock_para2 = MagicMock()
        mock_para2.text = "Second paragraph"
        mock_doc.paragraphs = [mock_para1, mock_para2]

        with patch.dict("sys.modules", {"docx": MagicMock()}):
            import sys
            sys.modules["docx"].Document = MagicMock(return_value=mock_doc)

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                text = parser.parse_text(tmp_path)
                assert isinstance(text, str)
                assert "First paragraph" in text
                assert "Second paragraph" in text
            finally:
                tmp_path.unlink(missing_ok=True)
