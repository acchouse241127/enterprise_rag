"""Tests for Docling PDF parser and parser factory.

Author: C2
Date: 2026-03-06
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.document_parser.factory import ParserFactory, get_parser
from app.document_parser.models import ContentType, ParsedContent

# Check if Docling is available
try:
    import docling.document_converter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Skip Docling-specific tests if not installed
skip_if_no_docling = pytest.mark.skipif(
    not DOCLING_AVAILABLE,
    reason="Docling not installed. Install with: pip install docling"
)


@skip_if_no_docling
class TestDoclingPdfParser:
    """Test Docling PDF parser functionality."""

    @pytest.fixture
    def sample_pdf_path(self):
        """Create a minimal PDF for testing."""
        # This would normally be a real PDF file
        # For now, we'll mock the Docling behavior
        return Path("/tmp/sample.pdf")

    def test_parser_initialization(self):
        """Test that DoclingPdfParser can be initialized."""
        from app.document_parser.docling_pdf_parser import DoclingPdfParser

        parser = DoclingPdfParser(ocr_enabled=True)
        assert parser.ocr_enabled is True

    def test_parser_initialization_without_ocr(self):
        """Test DoclingPdfParser with OCR disabled."""
        from app.document_parser.docling_pdf_parser import DoclingPdfParser

        parser = DoclingPdfParser(ocr_enabled=False)
        assert parser.ocr_enabled is False

    @patch("app.document_parser.docling_pdf_parser.DocumentConverter")
    def test_parse_returns_parsed_content_list(self, mock_converter):
        """Test that parse() returns list of ParsedContent."""
        from app.document_parser.docling_pdf_parser import DoclingPdfParser

        # Mock Docling result
        mock_result = Mock()
        mock_doc = Mock()
        mock_result.document = mock_doc
        mock_converter.return_value.convert.return_value = mock_result

        # Mock document items
        mock_item = Mock()
        mock_item.label = "text"
        mock_item.text = "Sample text content"
        mock_item.prov = {"page_no": 1}
        mock_doc.iterate_items.return_value = [mock_item]

        parser = DoclingPdfParser()
        result = parser.parse(Path("test.pdf"))

        assert len(result) == 1
        assert result[0].content_type == ContentType.TEXT
        assert result[0].text == "Sample text content"
        assert result[0].page_number == 1

    @patch("app.document_parser.docling_pdf_parser.DocumentConverter")
    def test_parse_table_content(self, mock_converter):
        """Test that tables are parsed correctly."""
        from app.document_parser.docling_pdf_parser import DoclingPdfParser

        # Mock Docling result
        mock_result = Mock()
        mock_doc = Mock()
        mock_result.document = mock_doc
        mock_converter.return_value.convert.return_value = mock_result

        # Mock table item
        mock_table = Mock()
        mock_table.label = "table"
        mock_table.text = "Cell1\tCell2"
        mock_table.export_to_markdown.return_value = "| A | B |"
        mock_table.prov = {"page_no": 1, "id": "table1"}
        mock_doc.iterate_items.return_value = [mock_table]

        parser = DoclingPdfParser()
        result = parser.parse(Path("test.pdf"))

        assert len(result) == 1
        assert result[0].content_type == ContentType.TABLE
        assert "table_markdown" in result[0].metadata
        assert result[0].metadata["table_markdown"] == "| A | B |"

    @patch("app.document_parser.docling_pdf_parser.DocumentConverter")
    def test_parse_formula_content(self, mock_converter):
        """Test that formulas are parsed correctly."""
        from app.document_parser.docling_pdf_parser import DoclingPdfParser

        # Mock Docling result
        mock_result = Mock()
        mock_doc = Mock()
        mock_result.document = mock_doc
        mock_converter.return_value.convert.return_value = mock_result

        # Mock formula item
        mock_formula = Mock()
        mock_formula.label = "formula"
        mock_formula.text = "E=mc^2"
        mock_formula.prov = {"page_no": 1}
        mock_doc.iterate_items.return_value = [mock_formula]

        parser = DoclingPdfParser()
        result = parser.parse(Path("test.pdf"))

        assert len(result) == 1
        assert result[0].content_type == ContentType.EQUATION
        assert "latex" in result[0].metadata
        assert result[0].metadata["latex"] == "E=mc^2"

    @patch("app.document_parser.docling_pdf_parser.DocumentConverter")
    def test_parse_image_content(self, mock_converter):
        """Test that images are parsed correctly."""
        from app.document_parser.docling_pdf_parser import DoclingPdfParser

        # Mock Docling result
        mock_result = Mock()
        mock_doc = Mock()
        mock_result.document = mock_doc
        mock_converter.return_value.convert.return_value = mock_result

        # Mock image item
        mock_image = Mock()
        mock_image.label = "picture"
        mock_image.text = "Image caption"
        mock_image.prov = {"page_no": 2, "id": "img1"}
        mock_doc.iterate_items.return_value = [mock_image]

        parser = DoclingPdfParser()
        result = parser.parse(Path("test.pdf"))

        assert len(result) == 1
        assert result[0].content_type == ContentType.IMAGE
        assert "image_path" in result[0].metadata


class TestParserFactory:
    """Test parser factory functionality."""

    @pytest.fixture(autouse=True)
    def reset_factory(self):
        """Reset factory instances before each test."""
        ParserFactory.clear_instances()
        yield
        ParserFactory.clear_instances()

    def test_get_pdf_parser_docling_backend(self):
        """Test getting Docling parser when configured."""
        with patch("app.document_parser.factory.settings") as mock_settings:
            mock_settings.pdf_parser_backend = "docling"
            mock_settings.docling_ocr_enabled = True
            from app.document_parser.docling_pdf_parser import DOCLING_AVAILABLE

            if DOCLING_AVAILABLE:
                parser = ParserFactory._get_pdf_parser()
                assert parser.__class__.__name__ == "DoclingPdfParser"

    def test_get_pdf_parser_legacy_backend(self):
        """Test getting legacy parser when configured."""
        with patch("app.document_parser.factory.settings") as mock_settings:
            mock_settings.pdf_parser_backend = "legacy"
            parser = ParserFactory._get_pdf_parser()
            assert parser.__class__.__name__ == "PdfDocumentParser"

    def test_get_parser_by_extension(self):
        """Test getting parser by file extension."""
        from app.document_parser import PdfDocumentParser

        parser = ParserFactory.get_parser("test.pdf")
        assert isinstance(parser, (PdfDocumentParser, type(Mock())))

    def test_get_parser_unsupported_type(self):
        """Test that unsupported file types raise error."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            ParserFactory.get_parser("test.unknown")

    def test_is_supported(self):
        """Test file type support checking."""
        assert ParserFactory.is_supported("test.pdf") is True
        assert ParserFactory.is_supported("test.txt") is True
        assert ParserFactory.is_supported("test.jpg") is True
        assert ParserFactory.is_supported("test.mp4") is True
        assert ParserFactory.is_supported("test.unknown") is False

    def test_get_supported_extensions(self):
        """Test getting list of supported extensions."""
        extensions = ParserFactory.get_supported_extensions()
        assert ".pdf" in extensions
        assert ".txt" in extensions
        assert ".docx" in extensions
        assert ".xlsx" in extensions
        assert ".pptx" in extensions
        assert ".png" in extensions
        assert ".mp3" in extensions

    def test_singleton_pattern(self):
        """Test that factory uses singleton pattern."""
        from app.document_parser import TxtDocumentParser

        parser1 = ParserFactory._get_or_create_instance(TxtDocumentParser)
        parser2 = ParserFactory._get_or_create_instance(TxtDocumentParser)
        assert parser1 is parser2

    def test_clear_instances(self):
        """Test clearing factory instances."""
        from app.document_parser import TxtDocumentParser

        parser1 = ParserFactory._get_or_create_instance(TxtDocumentParser)
        ParserFactory.clear_instances()
        parser2 = ParserFactory._get_or_create_instance(TxtDocumentParser)
        assert parser1 is not parser2


class TestGetParserFunction:
    """Test the convenience get_parser function."""

    def test_get_parser_convenience(self):
        """Test get_parser() works as convenience function."""
        parser = get_parser("test.pdf")
        assert parser is not None

    def test_get_parser_with_path_object(self):
        """Test get_parser() accepts Path objects."""
        parser = get_parser(Path("test.txt"))
        assert parser is not None
