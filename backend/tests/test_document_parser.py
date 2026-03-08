"""Document parser factory tests."""

from pathlib import Path

from app.document_parser import get_parser_for_extension
from app.document_parser.models import ContentType


def test_parser_factory_mappings() -> None:
    """Test parser factory returns correct parsers."""
    assert get_parser_for_extension(".txt") is not None
    assert get_parser_for_extension(".md") is not None
    assert get_parser_for_extension(".pdf") is not None
    assert get_parser_for_extension(".docx") is not None
    assert get_parser_for_extension(".xlsx") is not None
    assert get_parser_for_extension(".pptx") is not None
    assert get_parser_for_extension(".png") is not None
    assert get_parser_for_extension(".unknown") is None


def test_txt_parser_parse_returns_list(tmp_path: Path) -> None:
    """Test TXT parser returns list of ParsedContent."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("line1\nline2", encoding="utf-8")

    parser = get_parser_for_extension(".txt")
    assert parser is not None
    contents = parser.parse(file_path)

    # New interface returns list[ParsedContent]
    assert isinstance(contents, list)
    assert len(contents) == 1
    assert contents[0].content_type == ContentType.TEXT
    assert "line1" in contents[0].text
    assert "line2" in contents[0].text


def test_txt_parser_parse_text_backward_compat(tmp_path: Path) -> None:
    """Test parse_text() method for backward compatibility."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("line1\nline2", encoding="utf-8")

    parser = get_parser_for_extension(".txt")
    assert parser is not None
    text = parser.parse_text(file_path)

    # parse_text() returns plain string
    assert isinstance(text, str)
    assert "line1" in text
    assert "line2" in text
