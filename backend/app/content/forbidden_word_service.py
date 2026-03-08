"""Forbidden word service for content filtering.

Features:
- Word detection and replacement
- Category-based filtering
- Knowledge base specific words
- Caching for performance

Author: C2
Date: 2026-03-03
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class FilterAction(str, Enum):
    """Action to take when forbidden word is detected."""

    REPLACE = "replace"
    BLOCK = "block"
    WARN = "warn"


@dataclass
class FilterResult:
    """Result of content filtering."""

    original_text: str
    filtered_text: str
    detected_words: list[dict] = field(default_factory=list)
    action_taken: str = "none"


# Global word cache
class _WordCache:
    """Thread-safe word cache with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        self._words: dict[str, dict] = {}
        self._last_update: float = 0
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    @property
    def words(self) -> dict:
        return self._words.copy()

    def is_valid(self) -> bool:
        """Check if cache is still valid."""
        return time.time() - self._last_update < self._ttl

    def update(self, words: dict) -> None:
        """Update cache with new words."""
        with self._lock:
            self._words = words.copy()
            self._last_update = time.time()

    def invalidate(self) -> None:
        """Invalidate cache."""
        with self._lock:
            self._last_update = 0


_word_cache = _WordCache(ttl_seconds=settings.forbidden_words_cache_ttl_seconds)


def get_cached_words() -> dict:
    """Get cached forbidden words, loading from DB if needed."""
    if _word_cache.is_valid():
        return _word_cache.words

    # Load from database
    words = _load_words_from_db()
    _word_cache.update(words)
    return words


def _load_words_from_db() -> dict:
    """Load forbidden words from database."""
    try:
        from app.core.database import SessionLocal
        from app.models import ForbiddenWord

        db = SessionLocal()
        try:
            words = {}
            for fw in db.query(ForbiddenWord).filter(ForbiddenWord.is_enabled == True).all():
                words[fw.word] = {
                    "replacement": fw.replacement,
                    "category": fw.category,
                    "kb_id": fw.knowledge_base_id,
                }
            logger.info(f"Loaded {len(words)} forbidden words from database")
            return words
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to load forbidden words from database: {e}")
        return _get_default_words()


def _get_default_words() -> dict:
    """Get default built-in forbidden words."""
    return {
        "最佳": {"replacement": "优秀", "category": "absolute", "kb_id": None},
        "第一": {"replacement": "领先", "category": "absolute", "kb_id": None},
        "唯一": {"replacement": "主要", "category": "absolute", "kb_id": None},
        "保本": {"replacement": None, "category": "misleading", "kb_id": None},
        "无风险": {"replacement": None, "category": "misleading", "kb_id": None},
        "必赚": {"replacement": None, "category": "misleading", "kb_id": None},
    }


def invalidate_cache() -> None:
    """Invalidate the word cache."""
    _word_cache.invalidate()


class ForbiddenWordFilter:
    """Filter for detecting and replacing forbidden words."""

    def __init__(
        self,
        enabled: Optional[bool] = None,
        kb_id: Optional[int] = None,
        default_action: Optional[str] = None,
    ):
        self._enabled = enabled if enabled is not None else settings.forbidden_words_enabled
        self._kb_id = kb_id
        self._default_action = default_action or settings.forbidden_words_default_action
        self._words: dict[str, str | None] = {}
        self._load_words()

    def _load_words(self) -> None:
        """Load words from cache."""
        cached = get_cached_words()
        for word, config in cached.items():
            kb_id = config.get("kb_id")
            # Include word if:
            # 1. It's a global word (kb_id is None)
            # 2. It's specific to this KB
            if kb_id is None or kb_id == self._kb_id:
                self._words[word] = config.get("replacement")

    def filter(self, text: str) -> FilterResult:
        """Filter forbidden words from text.

        Args:
            text: Text to filter

        Returns:
            FilterResult with filtered text and detected words
        """
        if not self._enabled:
            return FilterResult(
                original_text=text,
                filtered_text=text,
                detected_words=[],
                action_taken="none",
            )

        filtered_text = text
        detected_words = []

        for word, replacement in self._words.items():
            if word in filtered_text:
                detected_words.append({
                    "word": word,
                    "replacement": replacement,
                })

                if replacement:
                    filtered_text = filtered_text.replace(word, replacement)
                elif self._default_action == "block":
                    # Block: remove the word entirely
                    filtered_text = filtered_text.replace(word, "***")
                # else: warn only, don't modify

        action_taken = "replace" if detected_words else "none"

        return FilterResult(
            original_text=text,
            filtered_text=filtered_text,
            detected_words=detected_words,
            action_taken=action_taken,
        )

    def batch_filter(self, texts: list[str]) -> list[FilterResult]:
        """Filter multiple texts.

        Args:
            texts: List of texts to filter

        Returns:
            List of FilterResult objects
        """
        return [self.filter(text) for text in texts]

    def check(self, text: str) -> list[dict]:
        """Check text for forbidden words without filtering.

        Args:
            text: Text to check

        Returns:
            List of detected forbidden words
        """
        if not self._enabled:
            return []

        detected = []
        for word, replacement in self._words.items():
            if word in text:
                detected.append({
                    "word": word,
                    "replacement": replacement,
                    "count": text.count(word),
                })
        return detected


class ForbiddenWordService:
    """Service for managing forbidden words in database."""

    def get_all_words(self) -> dict:
        """Get all forbidden words."""
        return get_cached_words()

    def get_words_by_category(self, category: str) -> dict:
        """Get words filtered by category."""
        words = get_cached_words()
        return {
            word: config
            for word, config in words.items()
            if config.get("category") == category
        }

    def add_word(
        self,
        db,
        word: str,
        category: str,
        replacement: Optional[str] = None,
        kb_id: Optional[int] = None,
    ) -> Any:
        """Add a new forbidden word.

        Args:
            db: Database session
            word: Forbidden word
            category: Word category
            replacement: Replacement text (None to block)
            kb_id: Knowledge base ID (None for global)

        Returns:
            Created ForbiddenWord object
        """
        from app.models import ForbiddenWord

        fw = ForbiddenWord(
            word=word,
            category=category,
            replacement=replacement,
            knowledge_base_id=kb_id,
            is_enabled=True,
        )
        db.add(fw)
        db.commit()
        db.refresh(fw)

        # Invalidate cache
        invalidate_cache()

        logger.info(f"Added forbidden word: {word}")
        return fw

    def update_word(
        self,
        db,
        word_id: int,
        replacement: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> Any:
        """Update a forbidden word.

        Args:
            db: Database session
            word_id: Word ID
            replacement: New replacement text
            is_enabled: New enabled status

        Returns:
            Updated ForbiddenWord object or None
        """
        from app.models import ForbiddenWord

        fw = db.query(ForbiddenWord).filter(ForbiddenWord.id == word_id).first()
        if not fw:
            return None

        if replacement is not None:
            fw.replacement = replacement
        if is_enabled is not None:
            fw.is_enabled = is_enabled

        db.commit()
        db.refresh(fw)

        # Invalidate cache
        invalidate_cache()

        logger.info(f"Updated forbidden word id={word_id}")
        return fw

    def delete_word(self, db, word_id: int) -> bool:
        """Delete a forbidden word.

        Args:
            db: Database session
            word_id: Word ID

        Returns:
            True if deleted, False if not found
        """
        from app.models import ForbiddenWord

        fw = db.query(ForbiddenWord).filter(ForbiddenWord.id == word_id).first()
        if not fw:
            return False

        db.delete(fw)
        db.commit()

        # Invalidate cache
        invalidate_cache()

        logger.info(f"Deleted forbidden word id={word_id}")
        return True

    def batch_add_words(
        self,
        db,
        words: list[dict],
    ) -> int:
        """Add multiple forbidden words.

        Args:
            db: Database session
            words: List of word configs with word, category, replacement

        Returns:
            Number of words added
        """
        from app.models import ForbiddenWord

        count = 0
        for word_config in words:
            fw = ForbiddenWord(
                word=word_config["word"],
                category=word_config.get("category", "custom"),
                replacement=word_config.get("replacement"),
                is_enabled=True,
            )
            db.add(fw)
            count += 1

        db.commit()

        # Invalidate cache
        invalidate_cache()

        logger.info(f"Batch added {count} forbidden words")
        return count
