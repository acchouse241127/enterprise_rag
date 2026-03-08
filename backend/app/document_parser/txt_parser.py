"""Text parser implementation."""

from pathlib import Path

from .base import BaseDocumentParser
from .models import ContentType, ParsedContent


class TxtDocumentParser(BaseDocumentParser):
    """Parser for plain text files."""

    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse text file into structured content."""
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="gbk")

        return [
            ParsedContent(
                content_type=ContentType.TEXT,
                text=text,
            )
        ]
