"""
Utility modules.
"""

from .file_validator import (
    get_file_type_from_magic,
    is_supported_extension,
    validate_file_type,
)

__all__ = [
    "get_file_type_from_magic",
    "is_supported_extension",
    "validate_file_type",
]
