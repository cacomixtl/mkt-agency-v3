"""
guardrails.resilience — The Sentry.

Provides a ``resilient_call`` utility that wraps any async callable
(typically an LLM API invocation) with a standardized retry policy
using the ``tenacity`` library.

Configuration (sourced from CONTRACTS.GuardrailConfig):
    - Retry:  N attempts with exponential backoff.
    - Triggers:  Connection timeouts, rate limits (429), and
      provider "overloaded" messages.
    - Circuit Breaker:  After all retries exhausted, raises
      ``ProviderUnavailableError`` that the logic layer can use
      to signal "System Paused" in the UI.

Usage:
    from guardrails import resilient_call

    result = await resilient_call(
        llm.ainvoke,
        prompt,
        operation_name="creative_worker_llm",
    )
"""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    before_sleep_log,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from CONTRACTS import DEFAULT_GUARDRAILS

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ═══════════════════════════════════════════════════════════════════════════
# Custom Exception
# ═══════════════════════════════════════════════════════════════════════════


class ProviderUnavailableError(Exception):
    """Raised after all retry attempts are exhausted.

    The logic layer should catch this to transition the campaign
    to a ``failed`` stage and emit an SSE error event with code 503.

    Attributes:
        operation_name:  Human-readable label for the failed call.
        attempts:        Number of attempts made.
        last_error:      The exception from the final attempt.
    """

    def __init__(
        self,
        operation_name: str,
        attempts: int,
        last_error: BaseException | None = None,
    ) -> None:
        self.operation_name = operation_name
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Provider unavailable after {attempts} attempts "
            f"for '{operation_name}': {last_error}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Retry Predicate — what to retry on
# ═══════════════════════════════════════════════════════════════════════════

# Known "overloaded" messages from major LLM providers
_OVERLOADED_PATTERNS: list[str] = [
    "overloaded",
    "resource_exhausted",
    "capacity",
    "server is busy",
    "service unavailable",
    "temporarily unavailable",
    "internal server error",
    "503",
    "rate limit",
]


def _is_retryable(exc: BaseException) -> bool:
    """Determine if an exception warrants a retry.

    Retries on:
        - Connection/timeout errors (httpx, OSError, TimeoutError)
        - HTTP 429 (rate limit) responses
        - Provider "overloaded" messages in error text
    """
    # ── Connection-level errors ──
    if isinstance(
        exc,
        (
            ConnectionError,
            TimeoutError,
            OSError,
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
        ),
    ):
        return True

    # ── HTTP status-based errors ──
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code in (429, 503, 502, 500):
            return True

    # ── Check error message for overloaded patterns ──
    error_msg = str(exc).lower()
    for pattern in _OVERLOADED_PATTERNS:
        if pattern in error_msg:
            return True

    return False


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════


async def resilient_call(
    fn: Callable[..., Any],
    *args: Any,
    operation_name: str = "external_call",
    max_attempts: int | None = None,
    min_wait: float | None = None,
    max_wait: float | None = None,
    **kwargs: Any,
) -> Any:
    """Execute ``fn(*args, **kwargs)`` with retry + circuit breaker.

    Parameters:
        fn:              The async callable to invoke.
        *args:           Positional arguments forwarded to ``fn``.
        operation_name:  Label for logging and error messages.
        max_attempts:    Override for retry count (default: from GuardrailConfig).
        min_wait:        Override for minimum backoff seconds.
        max_wait:        Override for maximum backoff seconds.
        **kwargs:        Keyword arguments forwarded to ``fn``.

    Returns:
        The return value of ``fn``.

    Raises:
        ProviderUnavailableError:  After all retries are exhausted.
    """
    attempts = max_attempts or DEFAULT_GUARDRAILS.transient_retry_attempts
    wait_min = min_wait or DEFAULT_GUARDRAILS.transient_retry_min_wait
    wait_max = max_wait or DEFAULT_GUARDRAILS.transient_retry_max_wait

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(
                multiplier=1,
                min=wait_min,
                max=wait_max,
            ),
            retry=retry_if_exception(_is_retryable),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        ):
            with attempt:
                logger.debug(
                    "resilient_call attempt %d/%d for '%s'",
                    attempt.retry_state.attempt_number,
                    attempts,
                    operation_name,
                )
                result = await fn(*args, **kwargs)
                return result

    except RetryError as exc:
        last = exc.last_attempt.exception() if exc.last_attempt else None
        logger.error(
            "Circuit breaker tripped for '%s' after %d attempts: %s",
            operation_name,
            attempts,
            last,
        )
        raise ProviderUnavailableError(
            operation_name=operation_name,
            attempts=attempts,
            last_error=last,
        ) from exc

    except Exception as exc:
        # Non-retryable exceptions that escaped the retry loop
        if _is_retryable(exc):
            # Should not happen, but defensive
            raise ProviderUnavailableError(
                operation_name=operation_name,
                attempts=attempts,
                last_error=exc,
            ) from exc
        # Non-retryable → propagate immediately (e.g., auth errors)
        raise
