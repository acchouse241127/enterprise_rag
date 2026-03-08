"""Comprehensive tests for PII Anonymizer module.

Tests cover:
- PiiPatternDetector detection methods
- PiiAnonymizer anonymization functionality
- Custom rules
- PII restoration
- AnonymizationResult dataclass
"""

import pytest
from unittest.mock import MagicMock, patch

from app.security.pii_anonymizer import (
    DEFAULT_PII_PATTERNS,
    AnonymizationResult,
    PiiPatternDetector,
    PiiAnonymizer,
)


class TestAnonymizationResult:
    """Tests for AnonymizationResult dataclass."""

    def test_anonymization_result_creation(self):
        """Test creating AnonymizationResult instance."""
        result = AnonymizationResult(
            original_text="My phone is 13812345678",
            anonymized_text="My phone is <PHONE_0000>",
            detected_pii=[{
                "type": "phone",
                "value": "13812345678",
                "placeholder": "<PHONE_0000>",
                "start": 13,
                "end": 23,
            }],
            pii_map={"<PHONE_0000>": "13812345678"},
        )
        
        assert result.original_text == "My phone is 13812345678"
        assert result.anonymized_text == "My phone is <PHONE_0000>"
        assert len(result.detected_pii) == 1
        assert result.pii_map == {"<PHONE_0000>": "13812345678"}

    def test_anonymization_result_defaults(self):
        """Test AnonymizationResult with default values."""
        result = AnonymizationResult(
            original_text="test",
            anonymized_text="test",
        )
        
        assert result.detected_pii == []
        assert result.pii_map == {}


class TestPiiPatternDetector:
    """Tests for PiiPatternDetector."""

    def test_detector_init_default_patterns(self):
        """Test detector initialization with default patterns."""
        detector = PiiPatternDetector()
        assert detector._patterns == DEFAULT_PII_PATTERNS

    def test_detector_init_custom_patterns(self):
        """Test detector initialization with custom patterns."""
        custom_patterns = {
            "test_type": {
                "pattern": r"TEST_\d+",
                "mask_format": "<TEST_****>",
            }
        }
        detector = PiiPatternDetector(patterns=custom_patterns)
        assert detector._patterns == custom_patterns

    def test_detect_phone_true(self):
        """Test detect_phone with phone number present."""
        detector = PiiPatternDetector()
        assert detector.detect_phone("My phone is 13812345678") is True

    def test_detect_phone_false(self):
        """Test detect_phone with no phone number."""
        detector = PiiPatternDetector()
        assert detector.detect_phone("Hello world") is False

    def test_detect_phone_invalid_prefix(self):
        """Test detect_phone with invalid phone prefix."""
        detector = PiiPatternDetector()
        assert detector.detect_phone("My phone is 12812345678") is False  # 12 is invalid

    def test_detect_phone_too_short(self):
        """Test detect_phone with too short number."""
        detector = PiiPatternDetector()
        assert detector.detect_phone("12345678") is False

    def test_detect_phone_too_long(self):
        """Test detect_phone with too long number."""
        detector = PiiPatternDetector()
        assert detector.detect_phone("138123456789") is False

    def test_detect_id_card_true(self):
        """Test detect_id_card with valid ID card."""
        detector = PiiPatternDetector()
        assert detector.detect_id_card("ID: 110101199001011234") is True

    def test_detect_id_card_with_x(self):
        """Test detect_id_card with X ending."""
        detector = PiiPatternDetector()
        assert detector.detect_id_card("11010119900101123X") is True
        assert detector.detect_id_card("11010119900101123x") is True

    def test_detect_id_card_false(self):
        """Test detect_id_card with no ID card."""
        detector = PiiPatternDetector()
        assert detector.detect_id_card("Hello world") is False

    def test_detect_id_card_wrong_length(self):
        """Test detect_id_card with wrong length."""
        detector = PiiPatternDetector()
        assert detector.detect_id_card("1234567890") is False

    def test_detect_bank_card_true(self):
        """Test detect_bank_card with 16 digit card."""
        detector = PiiPatternDetector()
        assert detector.detect_bank_card("Card: 6222021234567890") is True

    def test_detect_bank_card_19_digits(self):
        """Test detect_bank_card with 19 digit card."""
        detector = PiiPatternDetector()
        assert detector.detect_bank_card("6222021234567890123") is True

    def test_detect_bank_card_false(self):
        """Test detect_bank_card with no card number."""
        detector = PiiPatternDetector()
        assert detector.detect_bank_card("Hello world") is False

    def test_detect_bank_card_too_short(self):
        """Test detect_bank_card with too short number."""
        detector = PiiPatternDetector()
        assert detector.detect_bank_card("123456789012345") is False

    def test_detect_bank_card_too_long(self):
        """Test detect_bank_card with too long number."""
        detector = PiiPatternDetector()
        assert detector.detect_bank_card("12345678901234567890") is False

    def test_detect_email_true(self):
        """Test detect_email with valid email."""
        detector = PiiPatternDetector()
        assert detector.detect_email("Contact me at test@example.com") is True

    def test_detect_email_simple(self):
        """Test detect_email with simple email."""
        detector = PiiPatternDetector()
        assert detector.detect_email("test@example.com") is True

    def test_detect_email_false(self):
        """Test detect_email with no email."""
        detector = PiiPatternDetector()
        assert detector.detect_email("Hello world") is False

    def test_find_all_phone(self):
        """Test find_all for phone numbers."""
        detector = PiiPatternDetector()
        matches = detector.find_all(
            "Call 13812345678 or 13987654321",
            "phone"
        )
        
        assert len(matches) == 2
        assert matches[0][0] == "13812345678"
        assert matches[1][0] == "13987654321"
        # Verify start and end positions exist (actual values depend on regex match)
        assert len(matches[0]) == 3
        assert len(matches[1]) == 3

    def test_find_all_no_matches(self):
        """Test find_all with no matches."""
        detector = PiiPatternDetector()
        matches = detector.find_all("Hello world", "phone")
        
        assert matches == []

    def test_find_all_invalid_type(self):
        """Test find_all with invalid PII type."""
        detector = PiiPatternDetector()
        matches = detector.find_all("Hello world", "invalid_type")
        
        assert matches == []

    def test_find_all_id_card(self):
        """Test find_all for ID cards."""
        detector = PiiPatternDetector()
        matches = detector.find_all(
            "ID: 110101199001011234 and 220102198502025678",
            "id_card"
        )
        
        assert len(matches) == 2
        assert matches[0] == ("110101199001011234", 4, 22)
        assert matches[1] == ("220102198502025678", 27, 45)

    def test_find_all_email(self):
        """Test find_all for emails."""
        detector = PiiPatternDetector()
        matches = detector.find_all(
            "Email: test@example.com and user@test.org",
            "email"
        )
        
        assert len(matches) == 2

    def test_find_all_bank_card(self):
        """Test find_all for bank cards."""
        detector = PiiPatternDetector()
        matches = detector.find_all(
            "Card: 6222021234567890 and 6217000011111111",
            "bank_card"
        )
        
        assert len(matches) == 2


class TestPiiAnonymizer:
    """Tests for PiiAnonymizer."""

    def test_anonymizer_init_defaults(self):
        """Test PiiAnonymizer initialization with defaults."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            
            assert anonymizer.enabled is True
            assert "phone" in anonymizer.enabled_types
            assert "id_card" in anonymizer.enabled_types
            assert "bank_card" in anonymizer.enabled_types
            assert "email" in anonymizer.enabled_types

    def test_anonymizer_init_disabled(self):
        """Test PiiAnonymizer initialization with disabled."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = False
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            
            assert anonymizer.enabled is False

    def test_anonymizer_init_custom_types(self):
        """Test PiiAnonymizer initialization with custom types."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer(enabled_types=["phone", "email"])
            
            assert anonymizer.enabled_types == ["phone", "email"]

    def test_anonymizer_init_custom_rules(self):
        """Test PiiAnonymizer initialization with custom rules."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = [{
                "name": "custom_type",
                "pattern": r"CUSTOM_\d+",
                "mask_format": "<CUSTOM_****>",
            }]
            
            anonymizer = PiiAnonymizer()
            
            assert "custom_type" in anonymizer.enabled_types
            assert "custom_type" in anonymizer._patterns

    def test_anonymize_disabled(self):
        """Test anonymize when disabled."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = False
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("My phone is 13812345678")
            
            assert result.original_text == "My phone is 13812345678"
            assert result.anonymized_text == "My phone is 13812345678"
            assert result.detected_pii == []
            assert result.pii_map == {}

    def test_anonymize_no_pii(self):
        """Test anonymize with text containing no PII."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("Hello world")
            
            assert result.original_text == "Hello world"
            assert result.anonymized_text == "Hello world"
            assert result.detected_pii == []
            assert result.pii_map == {}

    def test_anonymize_single_phone(self):
        """Test anonymize with single phone number."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("Call me at 13812345678")
            
            assert result.anonymized_text == "Call me at <PHONE_0000>"
            assert len(result.detected_pii) == 1
            assert result.detected_pii[0]["type"] == "phone"
            assert result.detected_pii[0]["value"] == "13812345678"
            assert result.detected_pii[0]["placeholder"] == "<PHONE_0000>"
            assert result.pii_map["<PHONE_0000>"] == "13812345678"

    def test_anonymize_multiple_phones(self):
        """Test anonymize with multiple phone numbers."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("Call 13812345678 or 13987654321")
            
            # Since replacement is from end to start, the second phone gets PHONE_0000
            # and the first phone gets PHONE_0001
            assert "<PHONE_0000>" in result.anonymized_text
            assert "<PHONE_0001>" in result.anonymized_text
            assert len(result.detected_pii) == 2
            # Both numbers should be in the map
            assert "13812345678" in result.pii_map.values()
            assert "13987654321" in result.pii_map.values()

    def test_anonymize_single_id_card(self):
        """Test anonymize with single ID card."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("ID: 110101199001011234")
            
            assert result.anonymized_text == "ID: <ID_0000>"
            assert len(result.detected_pii) == 1
            assert result.detected_pii[0]["type"] == "id_card"
            assert result.pii_map["<ID_0000>"] == "110101199001011234"

    def test_anonymize_single_bank_card(self):
        """Test anonymize with single bank card."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("Card: 6222021234567890")
            
            assert result.anonymized_text == "Card: <BANK_0000>"
            assert len(result.detected_pii) == 1
            assert result.detected_pii[0]["type"] == "bank_card"

    def test_anonymize_single_email(self):
        """Test anonymize with single email."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("Email: test@example.com")
            
            assert result.anonymized_text == "Email: <EMAIL_0000>"
            assert len(result.detected_pii) == 1
            assert result.detected_pii[0]["type"] == "email"

    def test_anonymize_mixed_types(self):
        """Test anonymize with mixed PII types."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            text = "Contact 13812345678 or test@example.com"
            result = anonymizer.anonymize(text)
            
            # Both should be anonymized (order depends on replacement from end)
            assert "<PHONE_" in result.anonymized_text
            assert "<EMAIL_" in result.anonymized_text
            assert len(result.detected_pii) == 2
            # Verify both types are detected
            types = {pii["type"] for pii in result.detected_pii}
            assert "phone" in types
            assert "email" in types

    def test_anonymize_overlapping_matches(self):
        """Test anonymize handles overlapping matches correctly."""
        # Create a scenario where patterns might overlap
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            # Phone and ID card won't overlap, but test the logic
            text = "Phone 13812345678 ID 110101199001011234"
            result = anonymizer.anonymize(text)
            
            # Both should be detected
            assert len(result.detected_pii) == 2

    def test_anonymize_specific_types(self):
        """Test anonymize with specific enabled types."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer(enabled_types=["phone"])
            text = "Phone 13812345678 Email test@example.com"
            result = anonymizer.anonymize(text)
            
            # Only phone should be anonymized
            assert "<PHONE_0000>" in result.anonymized_text
            assert "<EMAIL_0000>" not in result.anonymized_text
            assert len(result.detected_pii) == 1

    def test_anonymize_custom_rule(self):
        """Test anonymize with custom rule."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = [{
                "name": "custom_id",
                "pattern": r"CID\d+",
                "mask_format": "<CUSTOM_ID_****>",
            }]
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("My CID is CID12345")
            
            assert "<CUSTOM_ID_0000>" in result.anonymized_text

    def test_restore(self):
        """Test restore method."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            text = "My phone is 13812345678"
            result = anonymizer.anonymize(text)
            
            restored = anonymizer.restore(
                result.anonymized_text,
                result.pii_map
            )
            
            assert restored == text

    def test_restore_partial_map(self):
        """Test restore with partial PII map."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            
            # Restore with only part of the map
            restored = anonymizer.restore(
                "My phone is <PHONE_0000> and <PHONE_0001>",
                {"<PHONE_0000>": "13812345678"}
            )
            
            assert "13812345678" in restored
            assert "<PHONE_0001>" in restored  # Not in map

    def test_restore_empty_map(self):
        """Test restore with empty map."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            restored = anonymizer.restore(
                "My phone is <PHONE_0000>",
                {}
            )
            
            assert restored == "My phone is <PHONE_0000>"

    def test_is_anonymized_true(self):
        """Test is_anonymized returns True for anonymized text."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            assert anonymizer.is_anonymized("My phone is <PHONE_0000>") is True

    def test_is_anonymized_false(self):
        """Test is_anonymized returns False for normal text."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            assert anonymizer.is_anonymized("My phone is 13812345678") is False

    def test_is_anonymized_multiple_types(self):
        """Test is_anonymized detects different placeholder types."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            assert anonymizer.is_anonymized("<PHONE_0000>") is True
            assert anonymizer.is_anonymized("<ID_0000>") is True
            assert anonymizer.is_anonymized("<BANK_0000>") is True
            assert anonymizer.is_anonymized("<EMAIL_0000>") is True

    def test_add_custom_rule(self):
        """Test add_custom_rule method."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            anonymizer.add_custom_rule(
                name="test_type",
                pattern=r"TEST_\d+",
                mask_format="<TEST_****>"
            )
            
            assert "test_type" in anonymizer._patterns
            assert "test_type" in anonymizer.enabled_types
            assert anonymizer._patterns["test_type"]["pattern"] == r"TEST_\d+"

    def test_add_custom_rule_default_mask_format(self):
        """Test add_custom_rule with default mask format."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            anonymizer.add_custom_rule(
                name="test_type",
                pattern=r"TEST_\d+"
            )
            
            assert anonymizer._patterns["test_type"]["mask_format"] == "<TEST_TYPE_****>"

    def test_add_custom_rule_anonymize(self):
        """Test anonymizing with newly added custom rule."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            anonymizer.add_custom_rule(
                name="custom_code",
                pattern=r"CODE\d+",
                mask_format="<CODE_****>"
            )
            
            result = anonymizer.anonymize("My CODE is CODE123")
            
            assert "<CODE_0000>" in result.anonymized_text

    def test_enabled_types_property(self):
        """Test enabled_types property returns copy."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            types1 = anonymizer.enabled_types
            types2 = anonymizer.enabled_types
            
            assert types1 == types2
            assert types1 is not types2  # Should be different objects

    def test_placeholder_uniqueness(self):
        """Test that placeholders are unique per detection."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("13812345678 13987654321 13611112222")
            
            # Each phone should have unique placeholder
            assert "<PHONE_0000>" in result.anonymized_text
            assert "<PHONE_0001>" in result.anonymized_text
            assert "<PHONE_0002>" in result.anonymized_text

    def test_replacement_from_end_to_start(self):
        """Test that replacements happen from end to start to preserve indices."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            # Text with phone at the end
            result = anonymizer.anonymize("123 and 13812345678")
            
            assert result.anonymized_text == "123 and <PHONE_0000>"

    def test_anonymization_result_details(self):
        """Test AnonymizationResult contains correct details."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            anonymizer = PiiAnonymizer()
            result = anonymizer.anonymize("Call 13812345678")
            
            pii = result.detected_pii[0]
            assert pii["type"] == "phone"
            assert pii["value"] == "13812345678"
            assert pii["placeholder"] == "<PHONE_0000>"
            assert "start" in pii
            assert "end" in pii
            assert isinstance(pii["start"], int)
            assert isinstance(pii["end"], int)

    def test_no_detection_for_disabled_type(self):
        """Test that disabled types are not detected."""
        with patch('app.security.pii_anonymizer.settings') as mock_settings:
            mock_settings.pii_anonymization_enabled = True
            mock_settings.pii_custom_rules = []
            
            # Disable phone, enable email
            anonymizer = PiiAnonymizer(enabled_types=["email"])
            text = "Phone 13812345678 Email test@example.com"
            result = anonymizer.anonymize(text)
            
            # Only email should be anonymized
            assert "13812345678" in result.anonymized_text  # Not masked
            assert "<EMAIL_0000>" in result.anonymized_text  # Masked
