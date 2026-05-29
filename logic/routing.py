"""
logic.routing — Conditional edge functions for the V3 Swarm graph.

These are pure functions that inspect the graph state and return
a string key used by ``graph.add_conditional_edges()`` to determine
the next node.  They contain ZERO business logic.

Dynamic Routing:
    The Supervisor Swarm relies on ``supervisor_router`` to direct
    traffic from the Manager hub to the specialized workers, or
    to the HITL approval gate.
"""

from __future__ import annotations

import logging
from typing import Any

from CONTRACTS import DEFAULT_GUARDRAILS

logger = logging.getLogger(__name__)


def supervisor_router(state: dict[str, Any]) -> str:
    """Supervisor routing logic from the Manager node.

    Returns:
        ``"creative_worker"`` → Needs a new draft or revision.
        ``"judge_worker"``    → Draft exists but lacks evaluation.
        ``"image_worker"``    → Draft passed but needs image generation.
        ``"wait_for_approval"`` → Draft passed, route to HITL gate.

    Decision matrix:
        1. stage == revising → creative_worker
        2. drafts == 0 → creative_worker
        3. content.vibe_score is None → judge_worker
        4. content.needs_revision == True → creative_worker / wait_for_approval (if max reached)
        5. content.needs_revision == False and no image_urls and stage != generating_image → image_worker
        6. Otherwise → wait_for_approval
    """
    if state.get("stage") == "revising":
        logger.info("Routing: CREATIVE (Stage is revising)")
        return "creative_worker"

    drafts = state.get("drafts", [])
    content = state.get("content")
    retry_count = state.get("retry_count", 0)
    max_revisions = DEFAULT_GUARDRAILS.max_revisions

    if not drafts:
        logger.info("Routing: CREATIVE (No drafts exist)")
        return "creative_worker"

    if content and content.vibe_score is None:
        logger.info("Routing: JUDGE (Draft needs evaluation)")
        return "judge_worker"

    if content and content.needs_revision:
        if retry_count < max_revisions:
            logger.info("Routing: CREATIVE (Draft needs revision)")
            return "creative_worker"
        else:
            logger.warning(
                "Routing: APPROVAL (Max revisions %d reached, forcing HITL)",
                max_revisions,
            )
            return "wait_for_approval"

    if content and content.needs_revision is False:
        if not content.image_urls and state.get("stage") != "generating_image":
            logger.info("Routing: IMAGE_WORKER (Draft passed, generating image)")
            return "image_worker"
        else:
            logger.info("Routing: APPROVAL (Draft passed, image already generated/exists)")
            return "wait_for_approval"

    logger.info("Routing: APPROVAL (Fallback)")
    return "wait_for_approval"


def approval_router(state: dict[str, Any]) -> str:
    """Approval routing logic from the wait_for_approval node.

    Returns:
        ``"manager_node"``    → Re-routing to the supervisor for revision.
        ``"publisher_node"``  → Approved, route to publishing.
    """
    stage = state.get("stage")
    if stage == "revising":
        logger.info("Approval Routing: MANAGER (Requesting revision)")
        return "manager_node"

    logger.info("Approval Routing: PUBLISHER (Approved/no revision)")
    return "publisher_node"
