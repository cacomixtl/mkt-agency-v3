"""
guardrails.contract_validator — Schema Guardian.

Provides a ``@validate_node_output`` decorator for LangGraph nodes.
The decorator intercepts the node's return value (a partial state dict)
and validates specific keys against their Pydantic model contracts
defined in CONTRACTS.py.

Design decisions:
    - The CONTRACT_MAP maps state-key names to Pydantic model classes.
    - Only keys present in BOTH the return dict AND the CONTRACT_MAP
      are validated — unknown keys pass through untouched.
    - Validation failures raise ContractViolationError immediately
      (fail fast) so the resilience layer can retry or escalate.
    - The decorator is async-aware and works with both sync and async
      LangGraph nodes.

Usage:
    from guardrails import validate_node_output

    @validate_node_output
    async def creative_worker_node(state: dict) -> dict:
        ...
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Type

from pydantic import BaseModel, ValidationError

from CONTRACTS import (
    Critique,
    ExecutiveBriefing,
    JudgeScores,
    MarketingContent,
    RevisionEntry,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Custom Exception
# ═══════════════════════════════════════════════════════════════════════════

class ContractViolationError(Exception):
    """Raised when a node's output fails Pydantic validation.

    Attributes:
        node_name:  The decorated function's ``__name__``.
        field:      The state key that failed validation.
        details:    The Pydantic ``ValidationError`` string.
    """

    def __init__(self, node_name: str, field: str, details: str) -> None:
        self.node_name = node_name
        self.field = field
        self.details = details
        super().__init__(
            f"ContractViolation in '{node_name}' on field '{field}': {details}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Contract Map — state key → Pydantic model
# ═══════════════════════════════════════════════════════════════════════════

CONTRACT_MAP: dict[str, Type[BaseModel]] = {
    "content": MarketingContent,
    "critique": Critique,
    "executive_briefing_obj": ExecutiveBriefing,
    "judge_scores": JudgeScores,
}
"""Maps state-dict keys to their expected Pydantic model.

Only keys listed here will be validated.  This keeps the decorator
agnostic — it doesn't need to know which node it's wrapping.
"""

# Keys whose values are lists of Pydantic models (validate each element)
CONTRACT_LIST_MAP: dict[str, Type[BaseModel]] = {
    "revision_history": RevisionEntry,
}


# ═══════════════════════════════════════════════════════════════════════════
# Validation Logic
# ═══════════════════════════════════════════════════════════════════════════

def _validate_output(node_name: str, output: dict[str, Any]) -> None:
    """Validate a node's return dict against the CONTRACT_MAP.

    Raises ContractViolationError on the FIRST failing field.
    """
    if not isinstance(output, dict):
        raise ContractViolationError(
            node_name=node_name,
            field="__return__",
            details=f"Node must return a dict, got {type(output).__name__}",
        )

    # ── Validate scalar Pydantic fields ──
    for key, model_cls in CONTRACT_MAP.items():
        value = output.get(key)
        if value is None:
            continue  # Field not in this node's return — skip

        # If already a valid model instance, skip re-validation
        if isinstance(value, model_cls):
            continue

        # If it's a dict, attempt model construction
        if isinstance(value, dict):
            try:
                model_cls.model_validate(value)
            except ValidationError as exc:
                raise ContractViolationError(
                    node_name=node_name,
                    field=key,
                    details=str(exc),
                ) from exc
        else:
            raise ContractViolationError(
                node_name=node_name,
                field=key,
                details=(
                    f"Expected {model_cls.__name__} or dict, "
                    f"got {type(value).__name__}"
                ),
            )

    # ── Validate list-of-model fields ──
    for key, model_cls in CONTRACT_LIST_MAP.items():
        values = output.get(key)
        if values is None:
            continue

        if not isinstance(values, list):
            raise ContractViolationError(
                node_name=node_name,
                field=key,
                details=f"Expected list, got {type(values).__name__}",
            )

        for idx, item in enumerate(values):
            if isinstance(item, model_cls):
                continue
            if isinstance(item, dict):
                try:
                    model_cls.model_validate(item)
                except ValidationError as exc:
                    raise ContractViolationError(
                        node_name=node_name,
                        field=f"{key}[{idx}]",
                        details=str(exc),
                    ) from exc
            else:
                raise ContractViolationError(
                    node_name=node_name,
                    field=f"{key}[{idx}]",
                    details=(
                        f"Expected {model_cls.__name__} or dict, "
                        f"got {type(item).__name__}"
                    ),
                )


# ═══════════════════════════════════════════════════════════════════════════
# Decorator
# ═══════════════════════════════════════════════════════════════════════════

def validate_node_output(fn: Callable) -> Callable:
    """Decorator that validates a LangGraph node's return value.

    Wraps both sync and async node functions.  Intercepts the return
    dict and runs ``_validate_output`` before passing the result
    downstream.

    Raises:
        ContractViolationError: If any mapped field fails validation.
    """
    import asyncio

    @functools.wraps(fn)
    async def _async_wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = await fn(*args, **kwargs)
        _validate_output(fn.__name__, result)
        logger.debug("Contract validation passed for node '%s'", fn.__name__)
        return result

    @functools.wraps(fn)
    def _sync_wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = fn(*args, **kwargs)
        _validate_output(fn.__name__, result)
        logger.debug("Contract validation passed for node '%s'", fn.__name__)
        return result

    if asyncio.iscoroutinefunction(fn):
        return _async_wrapper
    return _sync_wrapper
