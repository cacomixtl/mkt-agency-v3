"""
logic.nodes.approval — HITL Gate Node.

This node acts as the pause point before final deployment. It updates
the stage to 'awaiting_approval' and emits the final logs. The graph
is configured to interrupt AFTER this node, saving state to the
AsyncPostgresSaver.
"""

from __future__ import annotations

import logging
from typing import Any

from guardrails import validate_node_output

logger = logging.getLogger(__name__)


@validate_node_output
async def approval_node(state: dict[str, Any]) -> dict[str, Any]:
    """Human-in-the-loop gate."""
    campaign_id = state.get("campaign_id", "unknown")

    logs_out = [
        "[System] Draft passed all checks. "
        "Pausing swarm execution for Director approval (HITL Gate)."
    ]

    logger.info("Entering HITL approval gate  campaign=%s", campaign_id)

    return {
        "stage": "awaiting_approval",
        "logs": logs_out,
    }
