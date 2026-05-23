"""
logic.nodes.manager — Supervisor Node.

Acts as the central orchestrator (router) in the Supervisor Swarm pattern.
Logs the current routing state. The actual branching logic happens in `logic.routing`.

Contract compliance:
    - Returns partial state dict.
    - Wrapped in `@validate_node_output` shield.
"""

from __future__ import annotations

import logging
from typing import Any

from guardrails import validate_node_output

logger = logging.getLogger(__name__)


@validate_node_output
async def manager_node(state: dict[str, Any]) -> dict[str, Any]:
    """Supervisor router node.

    1. Logs the current swarm status.
    """
    state.get("persona")

    drafts = state.get("drafts", [])
    content = state.get("content")
    campaign_id = state.get("campaign_id", "unknown")

    logs_out: list[str] = []

    logs_out.append(
        f"[Manager] Swarm check-in — drafts: {len(drafts)}, "
        f"needs_revision: {content.needs_revision if content else 'N/A'}"
    )

    logger.info(
        "Manager node check-in  campaign=%s  drafts=%d",
        campaign_id,
        len(drafts),
    )

    return {
        "logs": logs_out,
    }
