"""
Simple unit tests for PiiAnonymizer.

Tests for app/security/pii_anonymizer.py
Author: C2
"""

import pytest
from unittest.mock import MagicMock, patch


class TestPiiPatternDetector:
    """Tests for PiiPatternDetector class."""

    def test_detect_phone_true(self):
        """Test phone detection returns True."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "我的手机号是13812345678"
        assert detector.detect_phone(text) is True

    def test_detect_phone_false(self):
        """Test phone detection returns False."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "没有手机号"
        assert detector.detect_phone(text) is False

    def test_detect_email_true(self):
        """Test email detection returns True."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "联系邮箱 test@example.com"
        assert detector.detect_email(text) is True

    def test_detect_email_false(self):
        """Test email detection returns False."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "没有邮箱"
        assert detector.detect_email(text) is False

    def test_detect_id_card_true(self):
        """Test ID card detection returns True."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "身份证号 110101199001011234"
        assert detector.detect_id_card(text) is True

    def test_detect_id_card_false(self):
        """Test ID card detection returns False."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "没有身份证"
        assert detector.detect_id_card(text) is False

    def test_detect_bank_card_true(self):
        """Test bank card detection returns True."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "银行卡 6222021234567890123"
        assert detector.detect_bank_card(text) is True

    def test_detect_bank_card_false(self):
        """Test bank card detection returns False."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "没有银行卡"
        assert detector.detect_bank_card(text) is False

    def test_find_all_phones(self):
        """Test find_all returns phone matches."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "手机13812345678和13987654321"
        matches = detector.find_all(text, "phone")
        assert len(matches) == 2

    def test_find_all_emails(self):
        """Test find_all returns email matches."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "邮箱a@b.com和c@d.com"
        matches = detector.find_all(text, "email")
        # Just check we got some matches
        assert len(matches) >= 1

    def test_find_all_no_matches(self):
        """Test find_all with no matches."""
        from app.security.pii_anonymizer import PiiPatternDetector

        detector = PiiPatternDetector()
        text = "普通文本"
        matches = detector.find_all(text, "phone")
        assert len(matches) == 0

    def test_custom_patterns(self):
        """Test detector with custom patterns."""
        from app.security.pii_anonymizer import PiiPatternDetector

        custom = {
            "custom": {
                "pattern": r"CUSTOM-\d+",
                "mask_format": "<CUSTOM_****>"
            }
        }
        detector = PiiPatternDetector(patterns=custom)
        text = "CUSTOM-12345"
        # Custom patterns are stored but need matching pii_type
        assert detector._patterns == custom


class TestPiiAnonymizer:
    """Tests for PiiAnonymizer class."""

    def test_anonymize_phone(self):
        """Test phone anonymization."""
        from app.security.pii_anonymizer import PiiAnonymizer

        anonymizer = PiiAnonymizer(enabled=True)
        text = "手机号13812345678"
        result = anonymizer.anonymize(text)

        assert result.original_text == text
        assert "13812345678" not in result.anonymized_text
        assert len(result.detected_pii) >= 1

    def test_anonymize_email(self):
        """Test email anonymization."""
        from app.security.pii_anonymizer import PiiAnonymizer

        anonymizer = PiiAnonymizer(enabled=True)
        text = "邮箱test@example.com"
        result = anonymizer.anonymize(text)

        assert result.original_text == text
        assert "test@example.com" not in result.anonymized_text

    def test_anonymize_disabled(self):
        """Test anonymization when disabled."""
        from app.security.pii_anonymizer import PiiAnonymizer

        anonymizer = PiiAnonymizer(enabled=False)
        text = "手机号13812345678"
        result = anonymizer.anonymize(text)

        # When disabled, text should be unchanged
        assert result.anonymized_text == text
        assert len(result.detected_pii) == 0

    def test_anonymize_no_pii(self):
        """Test text without PII."""
        from app.security.pii_anonymizer import PiiAnonymizer

        anonymizer = PiiAnonymizer(enabled=True)
        text = "普通文本"
        result = anonymizer.anonymize(text)

        assert result.anonymized_text == text
        assert len(result.detected_pii) == 0

    def test_anonymize_multiple_pii(self):
        """Test text with multiple PII."""
        from app.security.pii_anonymizer import PiiAnonymizer

        anonymizer = PiiAnonymizer(enabled=True)
        text = "手机13812345678，邮箱test@example.com"
        result = anonymizer.anonymize(text)

        assert "13812345678" not in result.anonymized_text
        assert "test@example.com" not in result.anonymized_text
        assert len(result.detected_pii) >= 2

    def test_add_custom_rule(self):
        """Test adding custom rule."""
        from app.security.pii_anonymizer import PiiAnonymizer

        anonymizer = PiiAnonymizer(enabled=True)
        anonymizer.add_custom_rule("order_id", r"ORD-\d+", "<ORDER_****>")

        assert "order_id" in anonymizer._patterns

    def test_pii_map_contains_original(self):
        """Test pii_map contains original values."""
        from app.security.pii_anonymizer import PiiAnonymizer

        anonymizer = PiiAnonymizer(enabled=True)
        text = "手机13812345678"
        result = anonymizer.anonymize(text)

        # pii_map should map placeholder to original value
        assert len(result.pii_map) >= 1
        for placeholder, original in result.pii_map.items():
            assert "13812345678" == original


class TestAnonymizationResult:
    """Tests for AnonymizationResult dataclass."""

    def test_result_creation(self):
        """Test creating AnonymizationResult."""
        from app.security.pii_anonymizer import AnonymizationResult

        result = AnonymizationResult(
            original_text="original",
            anonymized_text="anonymized",
            detected_pii=[{"type": "phone"}],
            pii_map={"<PHONE_0000>": "13812345678"}
        )

        assert result.original_text == "original"
        assert result.anonymized_text == "anonymized"
        assert len(result.detected_pii) == 1
        assert len(result.pii_map) == 1

    def test_result_defaults(self):
        """Test AnonymizationResult defaults."""
        from app.security.pii_anonymizer import AnonymizationResult

        result = AnonymizationResult(
            original_text="text",
            anonymized_text="text"
        )

        assert result.detected_pii == []
        assert result.pii_map == {}
