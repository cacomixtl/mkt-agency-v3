"""
tests.test_shield — Unit tests for the Guardrails Shield.

Verifies the structural validation and resilience layer.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from guardrails import (
    validate_node_output,
    ContractViolationError,
    resilient_call,
    ProviderUnavailableError,
    sanity_check,
    SanitizationError,
)
from CONTRACTS import MarketingContent


# ═══════════════════════════════════════════════════════════════════════════
# 1. Schema Guardian (Contract Validator) Tests
# ═══════════════════════════════════════════════════════════════════════════

def test_contract_validator_missing_key():
    """Simulate a node returning a dictionary with a missing key for MarketingContent."""
    
    @validate_node_output
    def dummy_node(state):
        return {
            "content": {
                "caption": "This is fine",
                # "image_prompt" is missing!
            }
        }
        
    with pytest.raises(ContractViolationError) as exc_info:
        dummy_node({})
        
    assert "image_prompt" in str(exc_info.value)
    assert "ContractViolation" in str(exc_info.value)


def test_contract_validator_success():
    """Simulate a node returning a valid dictionary."""
    
    @validate_node_output
    def dummy_node(state):
        return {
            "content": {
                "caption": "This is fine",
                "image_prompt": "A good image",
            }
        }
        
    result = dummy_node({})
    assert "content" in result
    assert result["content"]["caption"] == "This is fine"


# ═══════════════════════════════════════════════════════════════════════════
# 2. The Sentry (Resilience) Tests
# ═══════════════════════════════════════════════════════════════════════════

import httpx

@pytest.mark.asyncio
async def test_resilient_call_429_retry():
    """Simulate a 429 Rate Limit error triggering the tenacity retry loop."""
    attempts = 0
    
    async def failing_api_call():
        nonlocal attempts
        attempts += 1
        raise httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=httpx.Request("GET", "https://api.openai.com/v1/completions"),
            response=httpx.Response(429, request=httpx.Request("GET", "https://api.openai.com/v1/completions"))
        )

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await resilient_call(
            failing_api_call, 
            operation_name="test_429",
            max_attempts=3,
            min_wait=0.01,
            max_wait=0.05
        )
        
    assert attempts == 3
    assert "429" in str(exc_info.value)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Border Control (Sanitizer) Tests
# ═══════════════════════════════════════════════════════════════════════════

def test_sanitizer_refusal_catch():
    """Verify that a 'Refusal' string is caught by the sanitizer."""
    refusal_text = "I'm sorry, but as an AI language model I cannot assist with this prompt."
    
    with pytest.raises(SanitizationError) as exc_info:
        sanity_check(text=refusal_text)
        
    assert exc_info.value.check_type == "refusal"
    assert "as an ai language model" in str(exc_info.value).lower()

def test_sanitizer_empty_field():
    """Verify empty output veto for mandatory fields."""
    bad_data = {
        "caption": "   ",  # Just whitespace
        "image_prompt": "Valid prompt"
    }
    
    with pytest.raises(SanitizationError) as exc_info:
        sanity_check(
            data=bad_data, 
            mandatory_text_fields=["caption", "image_prompt"]
        )
        
    assert exc_info.value.check_type == "empty"
    assert "caption" in str(exc_info.value)
