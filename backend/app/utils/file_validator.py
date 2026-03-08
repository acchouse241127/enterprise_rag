"""
File type validation using Magic Numbers.

Uses file signatures to validate actual file types instead of relying on extensions.

Author: System
Date: 2026-03-07
"""

import logging
from typing import Optional

# Magic number signatures for common file types
MAGIC_NUMBERS = {
    # PDF
    b'%PDF': 'pdf',
    b'%PDF-': 'pdf',
    # Images
    b'\xFF\xD8\xFF': 'jpeg',
    b'\xFF\xD8\xFF\xE0': 'jpeg',
    b'\x89PNG\r\n\x1A\n': 'png',
    # ZIP (including DOCX, XLSX, PPTX)
    b'PK\x03\x04': 'zip',
    b'PK\x05\x06': 'zip',
    b'PK\x07\x08': 'zip',
    # OLE2 (DOC, XLS, PPT)
    b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'ole2',
}

# Extension to expected type mapping
EXTENSION_TYPE_MAP = {
    '.pdf': 'pdf',
    '.png': 'png',
    '.jpg': 'jpeg',
    '.jpeg': 'jpeg',
    '.docx': 'zip',
    '.xlsx': 'zip',
    '.pptx': 'zip',
    '.txt': 'text',
    '.md': 'text',
}

logger = logging.getLogger(__name__)


def get_file_type_from_magic(file_content: bytes) -> Optional[str]:
    """
    Detect file type from magic number.

    Args:
        file_content: First few bytes of the file

    Returns:
        Detected file type or None if not recognized
    """
    if not file_content or len(file_content) < 4:
        return None

    # Check each magic number signature
    for magic_signature, file_type in MAGIC_NUMBERS.items():
        if file_content.startswith(magic_signature):
            return file_type

    return None


def validate_file_type(file_content: bytes, filename: str) -> tuple[bool, Optional[str]]:
    """
    Validate file type matches extension using magic number.

    Args:
        file_content: First few bytes of the file
        filename: Filename with extension

    Returns:
        (is_valid, error_message)
    """
    import os
    ext = os.path.splitext(filename)[1].lower()

    # Get expected type from extension
    expected_type = EXTENSION_TYPE_MAP.get(ext)

    # If we don't have a magic number for this type, skip validation
    if expected_type is None:
        return True, None

    # Detect actual type from content
    actual_type = get_file_type_from_magic(file_content)

    if actual_type is None:
        return False, f"无法识别文件类型: {filename}"

    # Allow ZIP type for office documents (DOCX, XLSX, PPTX)
    if expected_type == 'zip' and ext in {'.docx', '.xlsx', '.pptx'}:
        return True, None

    # Check if actual type matches expected
    if actual_type != expected_type:
        logger.warning(
            "文件类型不匹配: 文件名=%s, 扩展名=%s, 期望=%s, 实际=%s",
            filename, ext, expected_type, actual_type
        )
        return False, f"文件类型不匹配: 扩展名是 {ext}，但实际文件类型是 {actual_type}"

    return True, None


def is_supported_extension(filename: str) -> bool:
    """
    Check if file extension is supported.

    Args:
        filename: Filename to check

    Returns:
        True if extension is supported
    """
    import os
    ext = os.path.splitext(filename)[1].lower()

    supported_extensions = {
        '.txt', '.md',
        '.doc', '.docx',
        '.xls', '.xlsx',
        '.ppt', '.pptx',
        '.pdf',
        '.png', '.jpg', '.jpeg',
    }

    return ext in supported_extensions
