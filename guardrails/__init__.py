"""
guardrails — Structural validation and resilience layer for Agency V3.

This package provides the defensive infrastructure that sits between
the LangGraph nodes and the outside world.  It owns:

    - contract_validator: Decorator-based output validation for nodes
    - resilience:         Retry/circuit-breaker wrappers for external calls
    - sanitizer:          Agnostic content-sanitization (LLM failure modes)
    - error_mapping:      Exception → UI-ready error code translation

Rules:
    1. ZERO stylistic checks — structure only.
    2. Every utility is importable by other agents.
    3. Fail fast, fail loud — never silently swallow errors.
"""

from guardrails.contract_validator import validate_node_output, ContractViolationError
from guardrails.resilience import resilient_call, ProviderUnavailableError
from guardrails.sanitizer import sanity_check, SanitizationError
from guardrails.error_mapping import ExceptionMapper

__all__ = [
    "validate_node_output",
    "ContractViolationError",
    "resilient_call",
    "ProviderUnavailableError",
    "sanity_check",
    "SanitizationError",
    "ExceptionMapper",
]
