"""Content filtering package for forbidden words.

Author: C2
Date: 2026-03-03
"""

from app.content.forbidden_word_service import (
    FilterAction,
    FilterResult,
    ForbiddenWordFilter,
    ForbiddenWordService,
    get_cached_words,
)

__all__ = [
    "ForbiddenWordService",
    "ForbiddenWordFilter",
    "FilterResult",
    "FilterAction",
    "get_cached_words",
]
