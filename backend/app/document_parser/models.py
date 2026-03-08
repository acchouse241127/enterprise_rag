"""Data models for structured document parsing.

Author: C2
Date: 2026-03-06
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContentType(Enum):
    """Content type enumeration for parsed document elements."""

    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    EQUATION = "equation"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class ParsedContent:
    """A structured content unit from document parsing.

    Represents a single piece of content extracted from a document,
    with type information and optional metadata.

    Attributes:
        content_type: The type of content (text, table, image, etc.)
        text: The main text content
        metadata: Additional information (e.g., table_markdown, vlm_description)
        page_number: Page number for source tracing (1-indexed)
        position: Position on page for "jump to source" feature
                  Format: {"x": int, "y": int, "width": int, "height": int}
    """

    content_type: ContentType
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    page_number: int | None = None
    position: dict[str, int] | None = None
