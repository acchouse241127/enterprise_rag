"""PII anonymizer service for detecting and masking sensitive data.

Supports:
- Phone numbers (Chinese mobile)
- ID cards (Chinese 18-digit)
- Bank cards (16-19 digits)
- Email addresses
- Custom regex patterns

Author: C2
Date: 2026-03-03
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# Default PII patterns
DEFAULT_PII_PATTERNS = {
    "phone": {
        "pattern": r"(?<![0-9])1[3-9]\d{9}(?![0-9])",
        "mask_format": "<PHONE_****>",
    },
    "id_card": {
        "pattern": r"(?<![0-9])\d{17}[\dXx](?![0-9])",
        "mask_format": "<ID_****>",
    },
    "bank_card": {
        "pattern": r"(?<![0-9])\d{16,19}(?![0-9])",
        "mask_format": "<BANK_****>",
    },
    "email": {
        "pattern": r"[\w.-]+@[\w.-]+\.\w+",
        "mask_format": "<EMAIL_****>",
    },
    # Note: address and name patterns are more complex and prone to false positives
    # They are disabled by default, enable with caution
}


@dataclass
class AnonymizationResult:
    """Result of PII anonymization."""

    original_text: str
    anonymized_text: str
    detected_pii: list[dict] = field(default_factory=list)
    pii_map: dict[str, str] = field(default_factory=dict)


class PiiPatternDetector:
    """Detector for PII patterns."""

    def __init__(self, patterns: Optional[dict] = None):
        self._patterns = patterns or DEFAULT_PII_PATTERNS

    def detect_phone(self, text: str) -> bool:
        """Check if text contains phone number."""
        pattern = self._patterns.get("phone", {}).get("pattern", r"1[3-9]\d{9}")
        return bool(re.search(pattern, text))

    def detect_id_card(self, text: str) -> bool:
        """Check if text contains ID card number."""
        pattern = self._patterns.get("id_card", {}).get("pattern", r"\d{17}[\dXx]")
        return bool(re.search(pattern, text))

    def detect_bank_card(self, text: str) -> bool:
        """Check if text contains bank card number."""
        pattern = self._patterns.get("bank_card", {}).get("pattern", r"\d{16,19}")
        return bool(re.search(pattern, text))

    def detect_email(self, text: str) -> bool:
        """Check if text contains email address."""
        pattern = self._patterns.get("email", {}).get("pattern", r"[\w.-]+@[\w.-]+\.\w+")
        return bool(re.search(pattern, text))

    def find_all(self, text: str, pii_type: str) -> list[tuple[str, int, int]]:
        """Find all occurrences of a PII type in text.

        Returns:
            List of (matched_text, start, end) tuples
        """
        pii_config = self._patterns.get(pii_type, {})
        pattern = pii_config.get("pattern", "")
        if not pattern:
            return []

        matches = []
        for match in re.finditer(pattern, text):
            matches.append((match.group(), match.start(), match.end()))
        return matches


class PiiAnonymizer:
    """Service for detecting and anonymizing PII in text."""

    def __init__(
        self,
        enabled: Optional[bool] = None,
        enabled_types: Optional[list[str]] = None,
        custom_rules: Optional[list[dict]] = None,
    ):
        self._enabled = enabled if enabled is not None else settings.pii_anonymization_enabled
        self._custom_rules = custom_rules or list(settings.pii_custom_rules)
        self._patterns = self._build_patterns()

        # If enabled_types not specified, enable all default types
        if enabled_types is None:
            self._enabled_types = list(DEFAULT_PII_PATTERNS.keys())
            # Also enable any custom rules
            for rule in self._custom_rules:
                name = rule.get("name")
                if name and name not in self._enabled_types:
                    self._enabled_types.append(name)
        else:
            self._enabled_types = enabled_types

        self._detector = PiiPatternDetector(self._patterns)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def enabled_types(self) -> list[str]:
        return self._enabled_types.copy()

    def _build_patterns(self) -> dict:
        """Build pattern dictionary from defaults and custom rules."""
        patterns = DEFAULT_PII_PATTERNS.copy()

        # Add custom rules
        for rule in self._custom_rules:
            name = rule.get("name")
            if name:
                patterns[name] = {
                    "pattern": rule.get("pattern", ""),
                    "mask_format": rule.get("mask_format", f"<{name.upper()}_****>"),
                }

        return patterns

    def add_custom_rule(
        self,
        name: str,
        pattern: str,
        mask_format: Optional[str] = None,
    ) -> None:
        """Add a custom PII detection rule."""
        self._patterns[name] = {
            "pattern": pattern,
            "mask_format": mask_format or f"<{name.upper()}_****>",
        }
        if name not in self._enabled_types:
            self._enabled_types.append(name)
        self._detector = PiiPatternDetector(self._patterns)

    def _generate_placeholder(self, pii_type: str, index: int) -> str:
        """Generate unique placeholder for PII."""
        mask_format = self._patterns.get(pii_type, {}).get(
            "mask_format", f"<{pii_type.upper()}_****>"
        )
        # Replace **** with index for uniqueness
        return mask_format.replace("****", f"{index:04d}")

    def anonymize(self, text: str) -> AnonymizationResult:
        """Anonymize PII in text.

        Args:
            text: Text to anonymize

        Returns:
            AnonymizationResult with anonymized text and PII map
        """
        if not self._enabled:
            return AnonymizationResult(
                original_text=text,
                anonymized_text=text,
                detected_pii=[],
                pii_map={},
            )

        detected_pii = []
        pii_map = {}
        placeholder_counter = 0

        # Collect all matches first
        all_matches = []
        for pii_type in self._enabled_types:
            if pii_type not in self._patterns:
                continue

            matches = self._detector.find_all(text, pii_type)
            for matched_text, start, end in matches:
                all_matches.append((pii_type, matched_text, start, end))

        # Sort by start position, then by length (longer first) to prioritize more specific matches
        all_matches.sort(key=lambda x: (x[2], -(x[3] - x[2])))

        # Remove overlapping matches (keep the first one encountered)
        non_overlapping = []
        covered_ranges = set()
        for pii_type, matched_text, start, end in all_matches:
            # Check if this range overlaps with any covered range
            overlaps = False
            for cs, ce in covered_ranges:
                if start < ce and end > cs:  # Overlaps
                    overlaps = True
                    break
            if not overlaps:
                non_overlapping.append((pii_type, matched_text, start, end))
                covered_ranges.add((start, end))

        # Sort by position (reverse) to replace from end to start
        non_overlapping.sort(key=lambda x: x[2], reverse=True)

        anonymized_text = text
        for pii_type, matched_text, start, end in non_overlapping:
            placeholder = self._generate_placeholder(pii_type, placeholder_counter)
            placeholder_counter += 1

            detected_pii.append({
                "type": pii_type,
                "value": matched_text,
                "placeholder": placeholder,
                "start": start,
                "end": end,
            })

            pii_map[placeholder] = matched_text
            anonymized_text = (
                anonymized_text[:start] + placeholder + anonymized_text[end:]
            )

        return AnonymizationResult(
            original_text=text,
            anonymized_text=anonymized_text,
            detected_pii=detected_pii,
            pii_map=pii_map,
        )

    def restore(self, text: str, pii_map: dict[str, str]) -> str:
        """Restore PII placeholders with original values.

        Args:
            text: Text with placeholders
            pii_map: Mapping from placeholder to original value

        Returns:
            Text with placeholders replaced by original values
        """
        restored = text
        for placeholder, original in pii_map.items():
            restored = restored.replace(placeholder, original)
        return restored

    def is_anonymized(self, text: str) -> bool:
        """Check if text contains PII placeholders."""
        # Check for common placeholder patterns
        placeholder_patterns = [
            r"<PHONE_\d+>",
            r"<ID_\d+>",
            r"<BANK_\d+>",
            r"<EMAIL_\d+>",
            r"<ADDRESS_\d+>",
            r"<NAME_\d+>",
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, text):
                return True
        return False
