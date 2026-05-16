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
        ``"wait_for_approval"`` → Draft passed, route to HITL gate.

    Decision matrix:
        1. drafts == 0 → creative_worker
        2. content.vibe_score is None → judge_worker
        3. content.needs_revision == True → creative_worker
        4. content.needs_revision == False → wait_for_approval
    """
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
                max_revisions
            )
            return "wait_for_approval"

    logger.info("Routing: APPROVAL (Draft passed)")
    return "wait_for_approval"
