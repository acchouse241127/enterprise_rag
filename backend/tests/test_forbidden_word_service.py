"""Tests for forbidden word service.

TDD Phase 1.4: Forbidden Word Service
- Word detection and filtering
- Word replacement
- Database management
- API endpoints

Author: C2
Date: 2026-03-03
"""

from unittest.mock import MagicMock, patch

import pytest


class TestForbiddenWordFilter:
    """Tests for forbidden word filtering."""

    @pytest.fixture
    def filter_service(self):
        """Create filter service instance."""
        from app.content.forbidden_word_service import ForbiddenWordFilter

        return ForbiddenWordFilter()

    def test_filter_single_word(self, filter_service):
        """Test filtering a single forbidden word."""
        # Add a test word
        filter_service._words = {"最佳": "优秀"}

        text = "这是我们最佳的产品"
        result = filter_service.filter(text)

        assert "最佳" not in result.filtered_text
        assert "优秀" in result.filtered_text

    def test_filter_multiple_words(self, filter_service):
        """Test filtering multiple forbidden words."""
        filter_service._words = {
            "最佳": "优秀",
            "第一": "领先",
            "唯一": "主要",
        }

        text = "我们是最佳、第一、唯一的选择"
        result = filter_service.filter(text)

        assert "最佳" not in result.filtered_text
        assert "第一" not in result.filtered_text
        assert "唯一" not in result.filtered_text

    def test_filter_with_no_replacement(self, filter_service):
        """Test filtering word with no replacement (block action)."""
        filter_service._words = {"保本": None}

        text = "这款产品保本保息"
        result = filter_service.filter(text)

        assert "保本" not in result.filtered_text or result.filtered_text == text

    def test_filter_no_match(self, filter_service):
        """Test filtering text with no forbidden words."""
        filter_service._words = {"最佳": "优秀"}

        text = "这是一个普通的产品"
        result = filter_service.filter(text)

        assert result.filtered_text == text
        assert len(result.detected_words) == 0

    def test_case_sensitive_filter(self, filter_service):
        """Test that filtering is case-sensitive."""
        filter_service._words = {"最佳": "优秀"}

        text = "这是最佳人选"
        result = filter_service.filter(text)

        assert "最佳" not in result.filtered_text


class TestForbiddenWordService:
    """Tests for forbidden word service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @patch("app.content.forbidden_word_service.get_cached_words")
    def test_get_all_words(self, mock_cache, mock_db):
        """Test getting all forbidden words."""
        from app.content.forbidden_word_service import ForbiddenWordService

        mock_cache.return_value = {
            "最佳": {"replacement": "优秀", "category": "absolute"},
            "第一": {"replacement": "领先", "category": "absolute"},
        }

        service = ForbiddenWordService()
        words = service.get_all_words()

        assert len(words) >= 2

    @patch("app.content.forbidden_word_service.get_cached_words")
    def test_get_words_by_category(self, mock_cache, mock_db):
        """Test getting words filtered by category."""
        from app.content.forbidden_word_service import ForbiddenWordService

        mock_cache.return_value = {
            "最佳": {"replacement": "优秀", "category": "absolute"},
            "保本": {"replacement": None, "category": "misleading"},
        }

        service = ForbiddenWordService()
        absolute_words = service.get_words_by_category("absolute")

        assert "最佳" in absolute_words
        assert "保本" not in absolute_words

    def test_add_word(self, mock_db):
        """Test adding a new forbidden word."""
        from app.content.forbidden_word_service import ForbiddenWordService
        from app.models import ForbiddenWord

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ForbiddenWordService()
        service.add_word(
            db=mock_db,
            word="测试禁用词",
            category="custom",
            replacement="替代词",
        )

        mock_db.add.assert_called_once()

    def test_update_word(self, mock_db):
        """Test updating a forbidden word."""
        from app.content.forbidden_word_service import ForbiddenWordService
        from app.models import ForbiddenWord

        mock_word = MagicMock()
        mock_word.word = "旧词"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_word
        mock_db.commit = MagicMock()

        service = ForbiddenWordService()
        service.update_word(
            db=mock_db,
            word_id=1,
            replacement="新替代词",
        )

        mock_db.commit.assert_called_once()

    def test_delete_word(self, mock_db):
        """Test deleting a forbidden word."""
        from app.content.forbidden_word_service import ForbiddenWordService

        mock_word = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_word
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()

        service = ForbiddenWordService()
        service.delete_word(db=mock_db, word_id=1)

        mock_db.delete.assert_called_once()


class TestFilterResult:
    """Tests for filter result dataclass."""

    def test_result_creation(self):
        """Test creating filter result."""
        from app.content.forbidden_word_service import FilterResult

        result = FilterResult(
            original_text="这是最佳的",
            filtered_text="这是优秀的",
            detected_words=[{"word": "最佳", "replacement": "优秀"}],
            action_taken="replace",
        )

        assert result.original_text == "这是最佳的"
        assert result.filtered_text == "这是优秀的"
        assert len(result.detected_words) == 1


class TestWordCaching:
    """Tests for word caching."""

    @patch("app.content.forbidden_word_service._word_cache")
    def test_cache_hit(self, mock_cache):
        """Test cache hit when getting words."""
        from app.content.forbidden_word_service import get_cached_words

        mock_cache.is_valid.return_value = True
        mock_cache.words = {"最佳": {"replacement": "优秀"}}

        result = get_cached_words()

        assert "最佳" in result

    @patch("app.content.forbidden_word_service._word_cache")
    @patch("app.content.forbidden_word_service._load_words_from_db")
    def test_cache_miss_loads_from_db(self, mock_load, mock_cache):
        """Test that cache miss loads from database."""
        from app.content.forbidden_word_service import get_cached_words

        mock_cache.is_valid.return_value = False
        mock_load.return_value = {"第一": {"replacement": "领先"}}
        mock_cache.update = MagicMock()

        result = get_cached_words()

        mock_load.assert_called_once()


class TestFilterAction:
    """Tests for filter actions."""

    def test_replace_action(self):
        """Test replace action."""
        from app.content.forbidden_word_service import FilterAction

        assert FilterAction.REPLACE.value == "replace"

    def test_block_action(self):
        """Test block action."""
        from app.content.forbidden_word_service import FilterAction

        assert FilterAction.BLOCK.value == "block"

    def test_warn_action(self):
        """Test warn action."""
        from app.content.forbidden_word_service import FilterAction

        assert FilterAction.WARN.value == "warn"


class TestKnowledgeBaseSpecificWords:
    """Tests for knowledge base specific forbidden words."""

    @patch("app.content.forbidden_word_service.get_cached_words")
    def test_kb_specific_filtering(self, mock_cache):
        """Test filtering with KB-specific words."""
        from app.content.forbidden_word_service import ForbiddenWordFilter

        mock_cache.return_value = {
            "通用词": {"replacement": "替代", "kb_id": None},
            "KB专属词": {"replacement": "KB替代", "kb_id": 1},
        }

        filter_service = ForbiddenWordFilter(kb_id=1)
        text = "通用词和KB专属词"
        result = filter_service.filter(text)

        # Both words should be filtered for KB 1
        assert "通用词" not in result.filtered_text
        assert "KB专属词" not in result.filtered_text

    @patch("app.content.forbidden_word_service.get_cached_words")
    def test_kb_exclusive_words(self, mock_cache):
        """Test that KB-specific words don't affect other KBs."""
        from app.content.forbidden_word_service import ForbiddenWordFilter

        mock_cache.return_value = {
            "KB专属词": {"replacement": "KB替代", "kb_id": 1},
        }

        # Filter for KB 2 should not filter KB 1's words
        filter_service = ForbiddenWordFilter(kb_id=2)
        text = "KB专属词"
        result = filter_service.filter(text)

        # KB 1's word should NOT be filtered for KB 2
        assert "KB专属词" in result.filtered_text


class TestBatchOperations:
    """Tests for batch operations."""

    def test_batch_add_words(self):
        """Test adding multiple words at once."""
        from app.content.forbidden_word_service import ForbiddenWordService

        mock_db = MagicMock()
        service = ForbiddenWordService()

        words = [
            {"word": "词1", "category": "absolute", "replacement": "替1"},
            {"word": "词2", "category": "misleading", "replacement": None},
        ]

        service.batch_add_words(mock_db, words)

        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

    def test_batch_check(self):
        """Test batch checking multiple texts."""
        from app.content.forbidden_word_service import ForbiddenWordFilter

        filter_service = ForbiddenWordFilter()
        filter_service._words = {"最佳": "优秀"}

        texts = ["这是最佳的", "普通文本", "又一个最佳的"]
        results = filter_service.batch_filter(texts)

        assert len(results) == 3
        assert "最佳" not in results[0].filtered_text
        assert results[1].filtered_text == "普通文本"
        assert "最佳" not in results[2].filtered_text


class TestDisabledFilter:
    """Tests for disabled filter."""

    def test_filter_disabled(self):
        """Test that disabled filter returns original text."""
        from app.content.forbidden_word_service import ForbiddenWordFilter

        filter_service = ForbiddenWordFilter(enabled=False)
        filter_service._words = {"最佳": "优秀"}

        text = "这是最佳的"
        result = filter_service.filter(text)

        # Should return original text unchanged
        assert result.filtered_text == text
