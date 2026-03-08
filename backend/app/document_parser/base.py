"""Base parser protocol for document parsing.

Author: C2
Date: 2026-03-06 (Updated for V2.1 multimodal parsing)
"""

from abc import ABC, abstractmethod
from pathlib import Path

from .models import ParsedContent


class BaseDocumentParser(ABC):
    """Document parser abstraction.

    All parsers should implement parse() to return structured content.
    Use parse_text() for backward compatibility with pure text output.
    """

    @abstractmethod
    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse input file and return structured content list.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of ParsedContent objects with type and metadata
        """
        raise NotImplementedError

    def parse_text(self, file_path: Path) -> str:
        """Parse file and return plain text only (backward compatibility).

        This method extracts only the text from parsed content,
        useful for simple use cases or legacy code.

        Args:
            file_path: Path to the file to parse

        Returns:
            Plain text string with all content concatenated
        """
        contents = self.parse(file_path)
        return "\n".join(c.text for c in contents if c.text.strip())
