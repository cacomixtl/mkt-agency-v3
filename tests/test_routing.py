"""
tests.test_routing — Unit tests for conditional routing.

Role: Staff Quality & Reliability Engineer
Objective: Mathematically prove routing states under various state conditions.
"""

import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from CONTRACTS import MarketingContent
from logic.routing import approval_router, supervisor_router


def test_supervisor_router_revising_stage():
    """Verify that stage='revising' routes back to creative worker."""
    state = {
        "stage": "revising",
        "drafts": [],
        "content": None,
    }
    assert supervisor_router(state) == "creative_worker"


def test_supervisor_router_no_drafts():
    """Verify that empty drafts list routes to creative worker."""
    state = {
        "stage": "draft",
        "drafts": [],
        "content": None,
    }
    assert supervisor_router(state) == "creative_worker"


def test_supervisor_router_judge_evaluation_needed():
    """Verify that a draft with no vibe score routes to judge."""
    content = MarketingContent(
        caption="A test caption",
        image_prompt="A test image prompt",
        vibe_score=None,
    )
    state = {
        "stage": "draft",
        "drafts": [content],
        "content": content,
    }
    assert supervisor_router(state) == "judge_worker"


def test_supervisor_router_image_generation_needed():
    """Verify that a passed draft without images routes to image worker."""
    content = MarketingContent(
        caption="A test caption",
        image_prompt="A test image prompt",
        vibe_score=8.5,
        needs_revision=False,
        image_urls=[],
    )
    state = {
        "stage": "reviewing",
        "drafts": [content],
        "content": content,
    }
    assert supervisor_router(state) == "image_worker"


def test_supervisor_router_image_generation_avoid_infinite_loop():
    """Verify that if we just came from image generation, we route to approval even if image fails."""
    content = MarketingContent(
        caption="A test caption",
        image_prompt="A test image prompt",
        vibe_score=8.5,
        needs_revision=False,
        image_urls=[],
    )
    state = {
        "stage": "generating_image",
        "drafts": [content],
        "content": content,
    }
    assert supervisor_router(state) == "wait_for_approval"


def test_supervisor_router_already_has_images():
    """Verify that a passed draft with images routes straight to approval."""
    content = MarketingContent(
        caption="A test caption",
        image_prompt="A test image prompt",
        vibe_score=8.5,
        needs_revision=False,
        image_urls=["/media/mock_image.png"],
    )
    state = {
        "stage": "reviewing",
        "drafts": [content],
        "content": content,
    }
    assert supervisor_router(state) == "wait_for_approval"


def test_approval_router_revising():
    """Verify approval_router routes to manager when stage is revising."""
    state = {"stage": "revising"}
    assert approval_router(state) == "manager_node"


def test_approval_router_approved():
    """Verify approval_router routes to publisher under standard resume."""
    state = {"stage": "approved"}
    assert approval_router(state) == "publisher_node"
