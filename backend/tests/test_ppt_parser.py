"""
Unit tests for PowerPoint document parser.

Tests for app/document_parser/ppt_parser.py
Author: C2
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestPptDocumentParser:
    """Tests for PptDocumentParser class."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()
        assert parser is not None

    def test_parse_pptx_file(self):
        """Test parsing a PPTX file."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()

        # Mock Presentation
        mock_prs = MagicMock()
        mock_slide1 = MagicMock()
        mock_shape1 = MagicMock()
        mock_shape1.text = "Hello World"
        mock_slide1.shapes = [mock_shape1]
        mock_prs.slides = [mock_slide1]

        # Patch at the pptx module level
        with patch.dict("sys.modules", {"pptx": MagicMock()}):
            import sys
            sys.modules["pptx"].Presentation = MagicMock(return_value=mock_prs)

            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[Slide] 1" in result
                assert "Hello World" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_multiple_slides(self):
        """Test parsing PPTX with multiple slides."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()

        mock_prs = MagicMock()

        # Slide 1
        mock_slide1 = MagicMock()
        mock_shape1 = MagicMock()
        mock_shape1.text = "Slide 1 Content"
        mock_slide1.shapes = [mock_shape1]

        # Slide 2
        mock_slide2 = MagicMock()
        mock_shape2 = MagicMock()
        mock_shape2.text = "Slide 2 Content"
        mock_slide2.shapes = [mock_shape2]

        mock_prs.slides = [mock_slide1, mock_slide2]

        with patch.dict("sys.modules", {"pptx": MagicMock()}):
            import sys
            sys.modules["pptx"].Presentation = MagicMock(return_value=mock_prs)

            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[Slide] 1" in result
                assert "[Slide] 2" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_empty_slide(self):
        """Test parsing slide with no shapes."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide.shapes = []
        mock_prs.slides = [mock_slide]

        with patch.dict("sys.modules", {"pptx": MagicMock()}):
            import sys
            sys.modules["pptx"].Presentation = MagicMock(return_value=mock_prs)

            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[Slide] 1" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_ppt_calls_conversion(self):
        """Test that .ppt files are converted to .pptx."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide.shapes = []
        mock_prs.slides = [mock_slide]

        with tempfile.NamedTemporaryFile(suffix=".ppt", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            converted_path = Path(str(tmp_path).replace(".ppt", "_converted.pptx"))

            # Create the converted file
            converted_path.touch()

            with patch("app.document_parser.legacy_office.convert_ppt_to_pptx") as mock_convert:
                mock_convert.return_value = converted_path

                with patch.dict("sys.modules", {"pptx": MagicMock()}):
                    import sys
                    sys.modules["pptx"].Presentation = MagicMock(return_value=mock_prs)

                    result = parser.parse(tmp_path)
                    mock_convert.assert_called_once()

            # Cleanup
            converted_path.unlink(missing_ok=True)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_parse_slide_index_starts_at_one(self):
        """Test that slide numbering starts at 1."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_shape = MagicMock()
        mock_shape.text = "First slide"
        mock_slide.shapes = [mock_shape]
        mock_prs.slides = [mock_slide]

        with patch.dict("sys.modules", {"pptx": MagicMock()}):
            import sys
            sys.modules["pptx"].Presentation = MagicMock(return_value=mock_prs)

            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "[Slide] 1" in result
                assert "[Slide] 0" not in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_strips_whitespace(self):
        """Test that text is stripped of whitespace."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_shape = MagicMock()
        mock_shape.text = "  Text with spaces  "
        mock_slide.shapes = [mock_shape]
        mock_prs.slides = [mock_slide]

        with patch.dict("sys.modules", {"pptx": MagicMock()}):
            import sys
            sys.modules["pptx"].Presentation = MagicMock(return_value=mock_prs)

            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "Text with spaces" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_shapes_without_text_attribute(self):
        """Test parsing slides with shapes that have no text attribute."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()

        mock_prs = MagicMock()
        mock_slide = MagicMock()

        # Shape without text attribute - use spec to prevent hasattr from finding it
        mock_shape1 = MagicMock()
        del mock_shape1.text  # Remove text attribute

        # Shape with valid text
        mock_shape2 = MagicMock()
        mock_shape2.text = "Valid text"

        mock_slide.shapes = [mock_shape1, mock_shape2]
        mock_prs.slides = [mock_slide]

        with patch.dict("sys.modules", {"pptx": MagicMock()}):
            import sys
            sys.modules["pptx"].Presentation = MagicMock(return_value=mock_prs)

            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                assert "Valid text" in result
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_parse_handles_none_text(self):
        """Test that None text values are handled gracefully."""
        from app.document_parser.ppt_parser import PptDocumentParser

        parser = PptDocumentParser()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_shape = MagicMock()
        mock_shape.text = None
        mock_slide.shapes = [mock_shape]
        mock_prs.slides = [mock_slide]

        with patch.dict("sys.modules", {"pptx": MagicMock()}):
            import sys
            sys.modules["pptx"].Presentation = MagicMock(return_value=mock_prs)

            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = parser.parse(tmp_path)
                # Should have slide marker but not crash
                assert "[Slide] 1" in result
            finally:
                tmp_path.unlink(missing_ok=True)
