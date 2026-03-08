"""Tests for ParsedContent and ContentType."""

import pytest

from app.document_parser.models import ContentType, ParsedContent


class TestContentType:
    """测试 ContentType 枚举."""

    def test_content_types_exist(self):
        """验证所有需要的内容类型都存在."""
        assert ContentType.TEXT.value == "text"
        assert ContentType.TABLE.value == "table"
        assert ContentType.IMAGE.value == "image"
        assert ContentType.EQUATION.value == "equation"
        assert ContentType.AUDIO.value == "audio"
        assert ContentType.VIDEO.value == "video"

    def test_content_type_from_string(self):
        """验证可以从字符串创建 ContentType."""
        assert ContentType("text") == ContentType.TEXT
        assert ContentType("table") == ContentType.TABLE
        assert ContentType("image") == ContentType.IMAGE


class TestParsedContent:
    """测试 ParsedContent 数据类."""

    def test_text_content_minimal(self):
        """测试最小化的文本内容."""
        content = ParsedContent(
            content_type=ContentType.TEXT,
            text="Hello World",
        )
        assert content.content_type == ContentType.TEXT
        assert content.text == "Hello World"
        assert content.metadata == {}
        assert content.page_number is None
        assert content.position is None

    def test_text_content_with_page(self):
        """测试带页码的文本内容."""
        content = ParsedContent(
            content_type=ContentType.TEXT,
            text="Page content",
            page_number=5,
        )
        assert content.page_number == 5

    def test_table_content_with_markdown(self):
        """测试带 Markdown 的表格内容."""
        content = ParsedContent(
            content_type=ContentType.TABLE,
            text="table data",
            metadata={"table_markdown": "| A | B |\n|---|---|\n| 1 | 2 |"},
            page_number=1,
        )
        assert content.content_type == ContentType.TABLE
        assert content.metadata["table_markdown"] == "| A | B |\n|---|---|\n| 1 | 2 |"

    def test_image_content_with_vlm_description(self):
        """测试带 VLM 描述的图片内容."""
        content = ParsedContent(
            content_type=ContentType.IMAGE,
            text="OCR extracted text",
            metadata={
                "image_path": "/path/to/image.png",
                "vlm_description": "A bar chart showing sales trends",
            },
        )
        assert content.metadata["vlm_description"] == "A bar chart showing sales trends"
        assert content.metadata["image_path"] == "/path/to/image.png"

    def test_equation_content_with_latex(self):
        """测试带 LaTeX 的公式内容."""
        content = ParsedContent(
            content_type=ContentType.EQUATION,
            text="E = mc²",
            metadata={"latex": r"E = mc^2"},
        )
        assert content.metadata["latex"] == r"E = mc^2"

    def test_content_with_position(self):
        """测试带位置信息的内容（用于跳转原文）."""
        content = ParsedContent(
            content_type=ContentType.TEXT,
            text="Some text",
            page_number=3,
            position={"x": 100, "y": 200, "width": 300, "height": 50},
        )
        assert content.position["x"] == 100
        assert content.position["y"] == 200

    def test_metadata_default_empty_dict(self):
        """验证 metadata 默认为空字典."""
        content = ParsedContent(
            content_type=ContentType.TEXT,
            text="test",
        )
        # 不应该共享引用
        content.metadata["new_key"] = "value"
        content2 = ParsedContent(
            content_type=ContentType.TEXT,
            text="test2",
        )
        assert content2.metadata == {}
