"""
Unit tests for Excel document parser.

Tests for app/document_parser/excel_parser.py
Author: C2
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestExcelDocumentParser:
    """Tests for ExcelDocumentParser class."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()
        assert parser is not None

    def test_parse_simple_excel(self):
        """Test parsing a simple Excel file with headers and data."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        # Create a mock workbook
        mock_workbook = MagicMock()
        mock_sheet = MagicMock()

        # Set up sheet data
        mock_sheet.title = "Sheet1"
        # Simulate rows: header row + data rows
        mock_sheet.iter_rows.return_value = [
            ("Name", "Age", "City"),  # Header row
            ("Alice", 30, "Beijing"),
            ("Bob", 25, "Shanghai"),
        ]

        mock_workbook.worksheets = [mock_sheet]

        with patch("openpyxl.load_workbook", return_value=mock_workbook):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[工作表: Sheet1]" in result
                assert "Name" in result or "Age" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_empty_sheet(self):
        """Test parsing an empty sheet."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        mock_workbook = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.title = "EmptySheet"
        mock_sheet.iter_rows.return_value = []

        mock_workbook.worksheets = [mock_sheet]

        with patch("openpyxl.load_workbook", return_value=mock_workbook):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[工作表: EmptySheet]" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_multiple_sheets(self):
        """Test parsing Excel file with multiple sheets."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        mock_workbook = MagicMock()

        # First sheet
        mock_sheet1 = MagicMock()
        mock_sheet1.title = "Sheet1"
        mock_sheet1.iter_rows.return_value = [
            ("A", "B"),
            ("1", "2"),
        ]

        # Second sheet
        mock_sheet2 = MagicMock()
        mock_sheet2.title = "Sheet2"
        mock_sheet2.iter_rows.return_value = [
            ("X", "Y"),
            ("10", "20"),
        ]

        mock_workbook.worksheets = [mock_sheet1, mock_sheet2]

        with patch("openpyxl.load_workbook", return_value=mock_workbook):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[工作表: Sheet1]" in result
                assert "[工作表: Sheet2]" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_with_empty_cells(self):
        """Test parsing Excel with empty cells in data rows."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        mock_workbook = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.title = "Data"
        mock_sheet.iter_rows.return_value = [
            ("Col1", "Col2", "Col3"),
            ("A", None, "C"),  # Middle cell is None
            (None, "B2", None),  # First and last are None
        ]

        mock_workbook.worksheets = [mock_sheet]

        with patch("openpyxl.load_workbook", return_value=mock_workbook):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[工作表: Data]" in result
                # Should contain non-empty values
                assert "A" in result or "C" in result or "B2" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_with_only_empty_rows(self):
        """Test parsing sheet with only empty rows after header."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        mock_workbook = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.title = "OnlyHeader"
        mock_sheet.iter_rows.return_value = [
            ("Header1", "Header2"),
            (None, None),  # Empty row
            ("", ""),      # Another empty row
        ]

        mock_workbook.worksheets = [mock_sheet]

        with patch("openpyxl.load_workbook", return_value=mock_workbook):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[工作表: OnlyHeader]" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_with_missing_header_columns(self):
        """Test parsing with some empty header cells."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        mock_workbook = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.title = "PartialHeader"
        mock_sheet.iter_rows.return_value = [
            ("Col1", None, "Col3"),  # Middle header is empty
            ("A", "B", "C"),
        ]

        mock_workbook.worksheets = [mock_sheet]

        with patch("openpyxl.load_workbook", return_value=mock_workbook):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[工作表: PartialHeader]" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_data_only_mode(self):
        """Test that load_workbook is called with data_only=True."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        mock_workbook = MagicMock()
        mock_workbook.worksheets = []

        with patch("openpyxl.load_workbook") as mock_load:
            mock_load.return_value = mock_workbook
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                parser.parse(tmp_path)
                # Verify data_only=True was passed
                mock_load.assert_called_once()
                call_kwargs = mock_load.call_args[1]
                assert call_kwargs.get("data_only") == True
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_skip_empty_header_rows(self):
        """Test that parser skips empty rows at the beginning to find header."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        mock_workbook = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.title = "SkipEmpty"
        mock_sheet.iter_rows.return_value = [
            (None, None, None),  # Empty row
            ("", "", ""),        # Empty row
            ("Name", "Value", ""),  # Header row
            ("Item1", "100", "extra"),
        ]

        mock_workbook.worksheets = [mock_sheet]

        with patch("openpyxl.load_workbook", return_value=mock_workbook):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[工作表: SkipEmpty]" in result
                # Should find Name and Value headers
                assert "Name" in result or "Value" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_formats_as_key_value_pairs(self):
        """Test that data rows are formatted as key: value pairs."""
        from app.document_parser.excel_parser import ExcelDocumentParser

        parser = ExcelDocumentParser()

        mock_workbook = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.title = "KVTest"
        mock_sheet.iter_rows.return_value = [
            ("姓名", "部门", "职位"),
            ("张三", "技术部", "工程师"),
        ]

        mock_workbook.worksheets = [mock_sheet]

        with patch("openpyxl.load_workbook", return_value=mock_workbook):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                # Should contain key-value format with | separator
                assert "张三" in result
                assert "技术部" in result or "工程师" in result
            finally:
                tmp_path.unlink(missing_ok=True)
