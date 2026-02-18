"""Base parser protocol for document parsing."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseDocumentParser(ABC):
    """Document parser abstraction."""

    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """Parse input file and return plain text."""
        raise NotImplementedError

