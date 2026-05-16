"""
logic.state — V3 Graph State with LangGraph Reducers.

This module defines ``V3GraphState``, the annotated TypedDict that
flows through the LangGraph StateGraph.  It wraps the semantic
contracts from CONTRACTS.py and adds LangGraph-specific reducer
annotations so that list fields APPEND rather than overwrite.

Reducer Strategy:
    - ``messages``, ``revision_history``, ``logs``, ``drafts`` → operator.add
      (each node returns NEW entries; LangGraph appends them)
    - All scalar fields → last-writer-wins (default behavior)

Contract Compliance:
    Every field present in CONTRACTS.V3AgencyState is preserved here
    with identical semantics.  ``logs`` is the only graph-internal
    addition (not exposed in the API envelope).
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Optional

from pydantic import BaseModel

from CONTRACTS import (
    CampaignStage,
    InteractionChannel,
    MarketingContent,
    PersonaConfig,
    PublishTarget,
    RevisionEntry,
)



class V3GraphState:
    """LangGraph-compatible state with reducer annotations.

    This is used as the schema argument to ``StateGraph(V3GraphState)``.
    LangGraph inspects ``__annotations__`` on the class to discover
    fields and their reducer functions.

    Fields annotated with ``Annotated[list[T], operator.add]`` are
    append-only — nodes return only the NEW items and LangGraph
    concatenates them onto the existing list.
    """

    # ── Core pipeline state (V2-compatible) ──
    messages: Annotated[list[Any], operator.add]
    persona: PersonaConfig
    content: Optional[MarketingContent]  # Pointer to latest draft for backwards compatibility
    feedback: Optional[str]
    retry_count: int

    # ── Cockpit fields (V2-compatible) ──
    executive_briefing: Optional[str]
    approval_mode: Optional[str]
    shadow_mode: bool

    # ── Error recovery (V2-compatible) ──
    last_error: Optional[str]

    # ── V3 additions ──
    campaign_id: Optional[str]
    stage: Optional[CampaignStage]
    revision_history: Annotated[list[RevisionEntry], operator.add]
    publish_targets: list[PublishTarget]
    interaction_channel: Optional[InteractionChannel]


    drafts: Annotated[list[MarketingContent], operator.add]

    # ── Graph-internal (not in CONTRACTS.py) ──
    logs: Annotated[list[str], operator.add]
