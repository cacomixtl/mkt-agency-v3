"""
guardrails.sanitizer — Border Control.

Agnostic content-sanitization that catches common LLM failure modes
BEFORE the output reaches Pydantic parsing or downstream nodes.

Detection layers:
    1. Refusal Patterns:  "As an AI language model", "I cannot assist".
    2. Structural Integrity:  Required JSON keys present in raw dicts.
    3. Empty Output:  Veto empty strings for mandatory fields.

Usage:
    from guardrails import sanity_check
    sanity_check(
        data=raw_output,
        required_keys=["caption", "image_prompt"],
        mandatory_text_fields=["caption", "image_prompt"],
    )
"""

from __future__ import annotations

import logging
import re
from typing import Any, Sequence

logger = logging.getLogger(__name__)


class SanitizationError(Exception):
    """Raised when LLM output fails a sanity check."""

    def __init__(self, check_type: str, details: str) -> None:
        self.check_type = check_type
        self.details = details
        super().__init__(f"SanitizationError [{check_type}]: {details}")


_REFUSAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"as an ai(?: language)? model", re.IGNORECASE),
    re.compile(r"i(?:'m| am) (?:just )?(?:a|an) (?:language )?model", re.IGNORECASE),
    re.compile(r"i cannot (?:assist|help|provide|create|generate)", re.IGNORECASE),
    re.compile(r"i(?:'m| am) unable to (?:assist|help|provide|create|generate)", re.IGNORECASE),
    re.compile(r"i(?:'m| am) not able to", re.IGNORECASE),
    re.compile(r"i can(?:no|')?t (?:do|fulfill|complete) that", re.IGNORECASE),
    re.compile(r"my (?:programming|guidelines|policy) (?:prevents?|doesn'?t allow)", re.IGNORECASE),
    re.compile(r"(?:sorry|apologies),? (?:but )?i (?:can(?:no|')?t|am unable)", re.IGNORECASE),
    re.compile(r"this (?:request|prompt) (?:violates|goes against)", re.IGNORECASE),
    re.compile(r"i(?:'m| am) designed to (?:be helpful|avoid|not)", re.IGNORECASE),
]


def detect_refusal(text: str) -> str | None:
    """Return the matched refusal phrase, or None if clean."""
    if not text:
        return None
    for pattern in _REFUSAL_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def check_required_keys(
    data: dict[str, Any], required_keys: Sequence[str],
) -> list[str]:
    """Return list of missing keys from data."""
    return [key for key in required_keys if key not in data]


def check_empty_fields(
    data: dict[str, Any], mandatory_text_fields: Sequence[str],
) -> list[str]:
    """Return field names that are empty or whitespace-only."""
    empty: list[str] = []
    for field_name in mandatory_text_fields:
        value = data.get(field_name)
        if value is None:
            empty.append(field_name)
        elif isinstance(value, str) and not value.strip():
            empty.append(field_name)
    return empty


def sanity_check(
    *,
    data: dict[str, Any] | None = None,
    text: str | None = None,
    required_keys: Sequence[str] | None = None,
    mandatory_text_fields: Sequence[str] | None = None,
) -> None:
    """Run all applicable sanity checks. Raises SanitizationError on failure."""
    # 1. Refusal detection on explicit text
    if text is not None:
        refusal_match = detect_refusal(text)
        if refusal_match:
            raise SanitizationError("refusal", f"LLM refusal detected: '{refusal_match}'")

    # 2. Refusal detection on dict string values
    if data is not None:
        for key, value in data.items():
            if isinstance(value, str):
                refusal_match = detect_refusal(value)
                if refusal_match:
                    raise SanitizationError(
                        "refusal",
                        f"LLM refusal in field '{key}': '{refusal_match}'",
                    )

    # 3. Structural integrity
    if data is not None and required_keys is not None:
        missing = check_required_keys(data, required_keys)
        if missing:
            raise SanitizationError("structure", f"Missing required keys: {missing}")

    # 4. Empty output
    if data is not None and mandatory_text_fields is not None:
        empty = check_empty_fields(data, mandatory_text_fields)
        if empty:
            raise SanitizationError("empty", f"Empty mandatory fields: {empty}")

    logger.debug("Sanity check passed")
