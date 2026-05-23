"""
guardrails.error_mapping — Error Mapping.

Translates technical exceptions into standardized UI-ready codes
defined in BRIDGE_SPEC.md §5.

Codes:
    - 422: Unprocessable Entity (Schema/Validation failures)
    - 429: Too Many Requests (Rate limits)
    - 409: Conflict (Aesthetic Drift/Max Revisions)
    - 503: Service Unavailable (Infrastructure/Provider failures)
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from guardrails.contract_validator import ContractViolationError
from guardrails.resilience import ProviderUnavailableError
from guardrails.sanitizer import SanitizationError

logger = logging.getLogger(__name__)


class ExceptionMapper:
    """Maps Python exceptions to standardized BRIDGE_SPEC errors."""

    @staticmethod
    def map_exception(exc: BaseException) -> tuple[int, str]:
        """Map an exception to a (status_code, message) tuple.

        Returns:
            (int, str): The HTTP status code and user-facing message.
        """
        # ── 422 Unprocessable Entity ──
        if isinstance(exc, (ContractViolationError, ValidationError)):
            return (422, f"Data Mismatch: {str(exc)}")

        if isinstance(exc, SanitizationError):
            return (422, f"Content Validation Failed: {exc.details}")

        # ── 503 Service Unavailable (and 429 via Tenacity) ──
        if isinstance(exc, ProviderUnavailableError):
            # Check if the underlying error was a rate limit
            if exc.last_error and "429" in str(exc.last_error):
                return (429, "Cooling Down: Provider rate limit exceeded")
            return (503, f"Offline: {str(exc)}")

        # ── 500 Internal Server Error (Fallback) ──
        return (500, f"Internal Error: {str(exc)}")

    @staticmethod
    def format_sse_error(
        exc: BaseException, node_name: str | None = None
    ) -> dict[str, Any]:
        """Format an exception into an SSEEventError compatible payload."""
        code, message = ExceptionMapper.map_exception(exc)
        return {
            "event_type": "error",
            "error_code": code,
            "message": message,
            "node_name": node_name,
        }
