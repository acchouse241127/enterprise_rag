"""Converter for transforming ParsedContent to text chunks.

Author: C2
Date: 2026-03-06
"""

from .models import ContentType, ParsedContent


def content_list_to_chunks(
    contents: list[ParsedContent],
    include_type_prefix: bool = True,
) -> list[str]:
    """Convert a list of ParsedContent to text chunks with type prefixes.

    Args:
        contents: List of ParsedContent objects
        include_type_prefix: Whether to add [表格], [图片], [公式] prefixes

    Returns:
        List of text chunks ready for chunking/embedding
    """
    chunks: list[str] = []

    for content in contents:
        text = content.text.strip()
        if not text:
            continue

        # Build the chunk text based on content type
        if content.content_type == ContentType.TEXT:
            # Plain text - no prefix
            chunks.append(text)

        elif content.content_type == ContentType.TABLE:
            # Table - use markdown if available, add prefix
            table_md = content.metadata.get("table_markdown", "")
            if table_md:
                final_text = table_md
            else:
                final_text = text

            if include_type_prefix:
                final_text = f"[表格]\n{final_text}"
            chunks.append(final_text)

        elif content.content_type == ContentType.IMAGE:
            # Image - combine VLM description with OCR text
            vlm_desc = content.metadata.get("vlm_description", "")
            if vlm_desc and text:
                final_text = f"{vlm_desc}\n{text}"
            elif vlm_desc:
                final_text = vlm_desc
            else:
                final_text = text

            if include_type_prefix:
                final_text = f"[图片] {final_text}"
            chunks.append(final_text)

        elif content.content_type == ContentType.EQUATION:
            # Equation - add prefix
            if include_type_prefix:
                final_text = f"[公式] {text}"
            else:
                final_text = text
            chunks.append(final_text)

        elif content.content_type == ContentType.AUDIO:
            # Audio transcription - no special prefix
            chunks.append(text)

        elif content.content_type == ContentType.VIDEO:
            # Video transcription - no special prefix
            chunks.append(text)

        else:
            # Unknown type - just use text
            chunks.append(text)

    return chunks


def get_content_metadata(contents: list[ParsedContent]) -> dict:
    """Extract metadata summary from parsed contents.

    Args:
        contents: List of ParsedContent objects

    Returns:
        Dict with flags for content types and page count
    """
    if not contents:
        return {
            "has_table": False,
            "has_image": False,
            "has_equation": False,
            "page_count": 1,
        }

    has_table = any(c.content_type == ContentType.TABLE for c in contents)
    has_image = any(c.content_type == ContentType.IMAGE for c in contents)
    has_equation = any(c.content_type == ContentType.EQUATION for c in contents)

    # Find max page number
    page_numbers = [c.page_number for c in contents if c.page_number is not None]
    page_count = max(page_numbers) if page_numbers else 1

    return {
        "has_table": has_table,
        "has_image": has_image,
        "has_equation": has_equation,
        "page_count": page_count,
    }
