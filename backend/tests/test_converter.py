"""Tests for content converter."""

import pytest

from app.document_parser.models import ContentType, ParsedContent
from app.document_parser.converter import (
    content_list_to_chunks,
    get_content_metadata,
)


class TestContentListToChunks:
    """测试 content_list_to_chunks 函数."""

    def test_empty_list(self):
        """空列表返回空列表."""
        assert content_list_to_chunks([]) == []

    def test_single_text_content(self):
        """单个文本内容."""
        contents = [
            ParsedContent(content_type=ContentType.TEXT, text="Hello World"),
        ]
        chunks = content_list_to_chunks(contents)
        assert chunks == ["Hello World"]

    def test_multiple_text_contents(self):
        """多个文本内容."""
        contents = [
            ParsedContent(content_type=ContentType.TEXT, text="Paragraph 1"),
            ParsedContent(content_type=ContentType.TEXT, text="Paragraph 2"),
        ]
        chunks = content_list_to_chunks(contents)
        assert len(chunks) == 2

    def test_table_content_with_prefix(self):
        """表格内容添加 [表格] 前缀."""
        contents = [
            ParsedContent(
                content_type=ContentType.TABLE,
                text="raw table data",
                metadata={"table_markdown": "| A | B |\n|---|---|"},
            ),
        ]
        chunks = content_list_to_chunks(contents)
        assert len(chunks) == 1
        assert chunks[0].startswith("[表格]")
        assert "| A | B |" in chunks[0]

    def test_table_content_without_markdown(self):
        """表格没有 Markdown 时使用原文本."""
        contents = [
            ParsedContent(
                content_type=ContentType.TABLE,
                text="raw table data",
                metadata={},
            ),
        ]
        chunks = content_list_to_chunks(contents)
        assert "[表格]" in chunks[0]
        assert "raw table data" in chunks[0]

    def test_image_content_with_vlm(self):
        """图片内容包含 VLM 描述."""
        contents = [
            ParsedContent(
                content_type=ContentType.IMAGE,
                text="OCR text from image",
                metadata={"vlm_description": "A bar chart showing trends"},
            ),
        ]
        chunks = content_list_to_chunks(contents)
        assert "[图片]" in chunks[0]
        assert "A bar chart showing trends" in chunks[0]
        assert "OCR text from image" in chunks[0]

    def test_image_content_without_vlm(self):
        """图片没有 VLM 描述时只有 OCR 文本."""
        contents = [
            ParsedContent(
                content_type=ContentType.IMAGE,
                text="OCR text only",
                metadata={},
            ),
        ]
        chunks = content_list_to_chunks(contents)
        assert "[图片]" in chunks[0]
        assert "OCR text only" in chunks[0]

    def test_equation_content(self):
        """公式内容添加 [公式] 前缀."""
        contents = [
            ParsedContent(
                content_type=ContentType.EQUATION,
                text="E = mc²",
                metadata={"latex": r"E = mc^2"},
            ),
        ]
        chunks = content_list_to_chunks(contents)
        assert chunks[0].startswith("[公式]")
        assert "E = mc²" in chunks[0]

    def test_mixed_contents(self):
        """混合内容类型."""
        contents = [
            ParsedContent(content_type=ContentType.TEXT, text="Intro text"),
            ParsedContent(
                content_type=ContentType.TABLE,
                text="table",
                metadata={"table_markdown": "| A | B |"},
            ),
            ParsedContent(content_type=ContentType.TEXT, text="Conclusion"),
        ]
        chunks = content_list_to_chunks(contents)
        assert len(chunks) == 3
        assert chunks[0] == "Intro text"
        assert "[表格]" in chunks[1]
        assert chunks[2] == "Conclusion"

    def test_empty_text_skipped(self):
        """空文本被跳过."""
        contents = [
            ParsedContent(content_type=ContentType.TEXT, text="Valid"),
            ParsedContent(content_type=ContentType.TEXT, text=""),
            ParsedContent(content_type=ContentType.TEXT, text="   "),
        ]
        chunks = content_list_to_chunks(contents)
        assert len(chunks) == 1
        assert chunks[0] == "Valid"

    def test_without_type_prefix(self):
        """禁用类型前缀."""
        contents = [
            ParsedContent(
                content_type=ContentType.TABLE,
                text="table data",
                metadata={},
            ),
        ]
        chunks = content_list_to_chunks(contents, include_type_prefix=False)
        assert "[表格]" not in chunks[0]
        assert chunks[0] == "table data"


class TestGetContentMetadata:
    """测试 get_content_metadata 函数."""

    def test_empty_list(self):
        """空列表返回默认元数据."""
        meta = get_content_metadata([])
        assert meta["has_table"] is False
        assert meta["has_image"] is False
        assert meta["has_equation"] is False
        assert meta["page_count"] == 1

    def test_detect_table(self):
        """检测表格."""
        contents = [
            ParsedContent(content_type=ContentType.TEXT, text="text"),
            ParsedContent(content_type=ContentType.TABLE, text="table"),
        ]
        meta = get_content_metadata(contents)
        assert meta["has_table"] is True
        assert meta["has_image"] is False

    def test_detect_image(self):
        """检测图片."""
        contents = [
            ParsedContent(content_type=ContentType.IMAGE, text="image"),
        ]
        meta = get_content_metadata(contents)
        assert meta["has_image"] is True
        assert meta["has_table"] is False

    def test_detect_equation(self):
        """检测公式."""
        contents = [
            ParsedContent(content_type=ContentType.EQUATION, text="eq"),
        ]
        meta = get_content_metadata(contents)
        assert meta["has_equation"] is True

    def test_page_count(self):
        """计算页数."""
        contents = [
            ParsedContent(content_type=ContentType.TEXT, text="p1", page_number=1),
            ParsedContent(content_type=ContentType.TEXT, text="p3", page_number=3),
            ParsedContent(content_type=ContentType.TEXT, text="p5", page_number=5),
        ]
        meta = get_content_metadata(contents)
        assert meta["page_count"] == 5

    def test_page_count_no_pages(self):
        """没有页码时默认为 1."""
        contents = [
            ParsedContent(content_type=ContentType.TEXT, text="no page"),
        ]
        meta = get_content_metadata(contents)
        assert meta["page_count"] == 1
