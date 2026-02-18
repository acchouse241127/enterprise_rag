"""Text parser implementation."""

from pathlib import Path

from .base import BaseDocumentParser


class TxtDocumentParser(BaseDocumentParser):
    """Parser for plain text files."""

    def parse(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="gbk")

