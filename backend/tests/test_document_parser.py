"""Document parser factory tests."""

from pathlib import Path

from app.document_parser import get_parser_for_extension


def test_parser_factory_mappings() -> None:
    assert get_parser_for_extension(".txt") is not None
    assert get_parser_for_extension(".md") is not None
    assert get_parser_for_extension(".pdf") is not None
    assert get_parser_for_extension(".docx") is not None
    assert get_parser_for_extension(".xlsx") is not None
    assert get_parser_for_extension(".pptx") is not None
    assert get_parser_for_extension(".png") is not None
    assert get_parser_for_extension(".unknown") is None


def test_txt_parser_parse(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("line1\nline2", encoding="utf-8")

    parser = get_parser_for_extension(".txt")
    assert parser is not None
    content = parser.parse(file_path)
    assert "line1" in content
    assert "line2" in content

