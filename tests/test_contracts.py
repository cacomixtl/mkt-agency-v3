"""
Pre-Flight CI/CD Smoke Tests: Contract Handshake Verification.

Role: Staff Quality & Reliability Engineer
Objective: Validate the foundational Pydantic models
in CONTRACTS.py against mock payloads
to ensure strict data integrity.
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from CONTRACTS import CampaignStartRequest, MarketingContent, PersonaConfig


def test_persona_config_handshake():
    """
    Validate the PersonaConfig (Brand Context replacement) against a valid mock payload.
    Ensure that missing required fields throw a validation error.
    """
    # 1. Valid Payload Test
    valid_payload = {
        "name": "Test Persona",
        "tone": "Analytical",
        "visual_style": "Minimalist",
        "brand_philosophy": "Less is more",
        # Default fields should automatically populate (e.g., visual_mood)
    }

    persona = PersonaConfig(**valid_payload)
    assert persona.name == "Test Persona"
    assert persona.tone == "Analytical"
    assert persona.visual_mood == "High-Contrast B&W"  # default

    # 2. Invalid Payload Test (Missing Required Fields)
    invalid_payload = {
        "name": "Missing Data Persona"
        # tone, visual_style, brand_philosophy are missing
    }

    with pytest.raises(ValidationError) as exc_info:
        PersonaConfig(**invalid_payload)

    error_str = str(exc_info.value)
    assert "tone" in error_str
    assert "visual_style" in error_str
    assert "brand_philosophy" in error_str


def test_marketing_content_handshake():
    """
    Validate the MarketingContent model against a mock payload.
    """
    # 1. Valid Payload Test
    valid_payload = {
        "caption": "This is a strictly tested caption.",
        "image_prompt": "A completely isolated test environment, harsh lighting.",
    }

    content = MarketingContent(**valid_payload)
    assert content.caption == valid_payload["caption"]
    assert content.aspect_ratio == "9:16"  # default

    # 2. Invalid Payload Test (Missing Required Fields)
    with pytest.raises(ValidationError) as exc_info:
        MarketingContent(caption="Missing image prompt")

    assert "image_prompt" in str(exc_info.value)


def test_campaign_start_request_handshake():
    """
    Validate the CampaignStartRequest model.
    """
    # 1. Valid Payload using Persona Name
    payload_name = {
        "persona_name": "Silicon Labor",
        "niche": "Cybernetic automation workflows",
    }
    req1 = CampaignStartRequest(**payload_name)
    assert req1.persona_name == "Silicon Labor"

    # 2. Missing Persona entirely
    with pytest.raises(ValidationError) as exc_info:
        CampaignStartRequest(niche="Testing missing persona")

    assert "Either persona_name or persona_config must be provided" in str(
        exc_info.value
    )
