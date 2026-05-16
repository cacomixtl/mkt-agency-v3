"""
Unit tests for ReAct agent tool functions.

Tests the individual tools in isolation by mocking the database layer,
verifying that each tool returns the expected structured output.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

# We need to mock settings before importing the module
import os
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("GEMINI_MODEL", "gemini-2.5-flash")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def set_current_phone():
    """Set the context variable phone number used by tools."""
    from app.services.agent.service import current_phone_var
    token = current_phone_var.set("+5215551234567")
    yield
    current_phone_var.reset(token)


@pytest.fixture
def mock_db_unavailable():
    """Mock database as unavailable — forces in-memory fallback."""
    with patch("app.core.database.is_db_available", return_value=False):
        yield


# ---------------------------------------------------------------------------
# Tests: check_pending_campaign
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_pending_campaign_none(mock_db_unavailable):
    """When no campaign exists, should return NO_PENDING_CAMPAIGN."""
    from app.services.agent.service import check_pending_campaign, _campaign_drafts

    _campaign_drafts.clear()
    result = await check_pending_campaign.ainvoke({})
    assert "NO_PENDING_CAMPAIGN" in result


@pytest.mark.asyncio
async def test_check_pending_campaign_exists(mock_db_unavailable):
    """When a draft exists in memory, should return its stage."""
    from app.services.agent.service import check_pending_campaign, _campaign_drafts

    _campaign_drafts["+5215551234567"] = {
        "stage": "preview",
        "strategy": {"format": "carousel"},
        "image_urls": ["http://example.com/img.png"],
    }

    result = await check_pending_campaign.ainvoke({})
    assert "PENDING_CAMPAIGN" in result
    assert "stage:preview" in result
    assert "has_images:yes" in result

    _campaign_drafts.clear()


# ---------------------------------------------------------------------------
# Tests: select_caption
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_select_caption_a(mock_db_unavailable):
    """Selecting option A should store the correct caption."""
    from app.services.agent.service import select_caption, _campaign_drafts

    _campaign_drafts["+5215551234567"] = {
        "stage": "preview",
        "strategy": {
            "caption_a": "Great product! 🎉",
            "caption_b": "Amazing deal! 🔥",
            "format": "carousel",
            "schedule": "2026-03-15 14:00",
        },
    }

    result = await select_caption.ainvoke({"option": "A"})
    assert "CAPTION_SELECTED" in result
    assert "option:A" in result
    assert _campaign_drafts["+5215551234567"]["selected_caption"] == "Great product! 🎉"
    assert _campaign_drafts["+5215551234567"]["stage"] == "schedule"

    _campaign_drafts.clear()


@pytest.mark.asyncio
async def test_select_caption_no_draft(mock_db_unavailable):
    """Selecting a caption with no draft should return an error."""
    from app.services.agent.service import select_caption, _campaign_drafts

    _campaign_drafts.clear()
    result = await select_caption.ainvoke({"option": "A"})
    assert "ERROR" in result


@pytest.mark.asyncio
async def test_select_caption_invalid_option(mock_db_unavailable):
    """Selecting an invalid option should return an error."""
    from app.services.agent.service import select_caption, _campaign_drafts

    _campaign_drafts["+5215551234567"] = {
        "stage": "preview",
        "strategy": {"caption_a": "A", "caption_b": "B"},
    }

    result = await select_caption.ainvoke({"option": "C"})
    assert "ERROR" in result

    _campaign_drafts.clear()


# ---------------------------------------------------------------------------
# Tests: schedule_campaign
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_campaign(mock_db_unavailable):
    """Scheduling should update the draft stage and schedule."""
    from app.services.agent.service import schedule_campaign, _campaign_drafts

    _campaign_drafts["+5215551234567"] = {
        "stage": "schedule",
        "strategy": {"schedule": "2026-03-10 14:00"},
    }

    result = await schedule_campaign.ainvoke({"date_time": "2026-03-15 10:00"})
    assert "CAMPAIGN_SCHEDULED" in result
    assert "SCHEDULE_APPROVED" in result
    assert _campaign_drafts["+5215551234567"]["stage"] == "scheduled"
    assert _campaign_drafts["+5215551234567"]["strategy"]["schedule"] == "2026-03-15 10:00"

    _campaign_drafts.clear()


# ---------------------------------------------------------------------------
# Tests: publish_campaign
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_publish_campaign_hitl(mock_db_unavailable):
    """Default publish should return HITL (requires confirmation)."""
    from app.services.agent.service import publish_campaign, _campaign_drafts

    _campaign_drafts["+5215551234567"] = {
        "stage": "scheduled",
        "strategy": {},
    }

    result = await publish_campaign.ainvoke({})
    assert "PUBLISH_NOW_HITL" in result

    _campaign_drafts.clear()


@pytest.mark.asyncio
async def test_publish_campaign_no_draft(mock_db_unavailable):
    """Publishing with no draft should return an error."""
    from app.services.agent.service import publish_campaign, _campaign_drafts

    _campaign_drafts.clear()
    result = await publish_campaign.ainvoke({})
    assert "ERROR" in result


# ---------------------------------------------------------------------------
# Tests: reject_and_regenerate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_no_draft(mock_db_unavailable):
    """Rejecting with no draft should return an error."""
    from app.services.agent.service import reject_and_regenerate, _campaign_drafts

    _campaign_drafts.clear()
    result = await reject_and_regenerate.ainvoke({})
    assert "ERROR" in result


# ---------------------------------------------------------------------------
# Tests: output guardrail
# ---------------------------------------------------------------------------

def test_output_guardrail_clean():
    """Clean response should pass the guardrail."""
    from app.services.agent.service import _check_output_guardrail
    assert _check_output_guardrail("Great campaign idea!") is None


def test_output_guardrail_blocked():
    """Response with blocked keyword should return fallback."""
    from app.services.agent.service import _check_output_guardrail, FALLBACK_MESSAGE
    result = _check_output_guardrail("As an AI, I cannot do that")
    assert result == FALLBACK_MESSAGE


# ---------------------------------------------------------------------------
# Tests: action extraction
# ---------------------------------------------------------------------------

def test_extract_action_campaign():
    """Campaign strategy tool output should map to campaign_preview."""
    from app.services.agent.service import _extract_action
    result = _extract_action(["CAMPAIGN_STRATEGY_CREATED|caption_a:test"], "")
    assert result == "campaign_preview"


def test_extract_action_schedule():
    """Schedule tool output should map to schedule_approved."""
    from app.services.agent.service import _extract_action
    result = _extract_action(["CAMPAIGN_SCHEDULED|datetime:2026-03-15 10:00|SCHEDULE_APPROVED"], "")
    assert result == "schedule_approved"


def test_extract_action_publish_hitl():
    """Publish HITL output should map to publish_hitl."""
    from app.services.agent.service import _extract_action
    result = _extract_action(["PUBLISH_NOW_HITL"], "")
    assert result == "publish_hitl"


def test_extract_action_none():
    """No tool outputs should return None (regular chat)."""
    from app.services.agent.service import _extract_action
    result = _extract_action([], "Hello!")
    assert result is None


# ---------------------------------------------------------------------------
# Tests: path classification
# ---------------------------------------------------------------------------

def test_classify_path_chat():
    """No tools used should classify as CHAT."""
    from app.services.agent.service import _classify_path
    assert _classify_path([], "") == (2, "CHAT")


def test_classify_path_campaign():
    """create_campaign_strategy tool should classify as CREATE_CAMPAIGN."""
    from app.services.agent.service import _classify_path
    assert _classify_path(["create_campaign_strategy"], "") == (3, "CREATE_CAMPAIGN")


def test_classify_path_publish():
    """publish_campaign tool should classify as PUBLISH."""
    from app.services.agent.service import _classify_path
    assert _classify_path(["publish_campaign"], "") == (6, "PUBLISH")
