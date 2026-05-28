"""
logic.nodes.publisher — Publisher Node (Stub).

Delivers approved marketing content to external platforms (Threads / Instagram).
In the current stub phase, the node operates in one of two modes:

  - SHADOW MODE (shadow_mode=True):  Content is logged and the stage is
    set to 'published'.  No external API call is made.  Safe for all
    environments including production while the Threads adapter is pending.

  - LIVE STUB (shadow_mode=False):  The Threads API is not yet wired.
    Stage is set to 'approved' to signal that content is cleared but
    undelivered.  A warning is logged so that operators can track the gap.

Contract compliance:
  - Reads:   campaign_id (str), shadow_mode (bool), content (MarketingContent),
             publish_targets (list[PublishTarget])
  - Writes:  stage ∈ {'published', 'approved'}, logs (list[str])
  - Stage produced: 'published' (shadow) | 'approved' (live stub)

Failure mode:
  - DB mirror update failures are caught and logged; they do NOT abort the
    node.  The publishing outcome is the authoritative result.
  - Unrecoverable errors (e.g. corrupted state) are allowed to propagate
    so that LangGraph can checkpoint the failure.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from guardrails import validate_node_output
from infrastructure.connection import get_db_session
from models.campaign import CampaignRecord
from sqlalchemy import update

logger = logging.getLogger(__name__)


@validate_node_output
async def publisher_node(state: dict[str, Any]) -> dict[str, Any]:
    """Publisher — delivers approved content or logs in shadow mode."""
    campaign_id = state.get("campaign_id", "unknown")
    shadow_mode = state.get("shadow_mode", True)
    content = state.get("content")

    logs_out: list[str] = []

    # ── Mode dispatch ──
    if shadow_mode:
        logs_out.append(
            "[Publisher] SHADOW MODE — content logged, no external API call executed."
        )
        logs_out.append(
            f"[Publisher] Content ready for Threads: "
            f"{len(content.caption) if content else 0} char caption"
        )
        new_stage = "published"
        logger.info(
            "Publisher node SHADOW MODE  campaign=%s",
            campaign_id,
        )
    else:
        logs_out.append(
            "[Publisher] STUB — Threads API not yet wired. Marking approved."
        )
        new_stage = "approved"
        logger.warning(
            "Publisher node stub — real Threads delivery not yet implemented"
            "  campaign=%s",
            campaign_id,
        )

    # ── DB Mirror Update (graceful — failure does not abort node) ──
    try:
        async with get_db_session() as session:
            stmt = (
                update(CampaignRecord)
                .where(CampaignRecord.thread_id == campaign_id)
                .values(
                    stage=new_stage,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await session.execute(stmt)
            logger.info(
                "DB stage mirror updated  campaign=%s  stage=%s",
                campaign_id,
                new_stage,
            )
    except Exception as db_err:
        logger.error(
            "Publisher DB mirror update failed  campaign=%s  error=%s",
            campaign_id,
            db_err,
        )
        logs_out.append(
            f"[Publisher] Warning: DB mirror update failed: {str(db_err)}"
        )
        # Do NOT re-raise — publishing result is what matters, not the mirror

    return {"stage": new_stage, "logs": logs_out}
