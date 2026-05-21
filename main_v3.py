"""
main_v3.py — V3 FastAPI Entry Point.

The "Handshake" layer between the React Director's Cockpit and the
Agency V3 persistent backend.  This file owns:

    - CORSMiddleware (BRIDGE_SPEC.md §6)
    - The /campaign/start endpoint (BRIDGE_SPEC.md §2)
    - The /campaign/{campaign_id}/state endpoint (BRIDGE_SPEC.md §2)
    - The /campaign/{campaign_id}/stream SSE endpoint (BRIDGE_SPEC.md §3)
    - The APIEnvelope response format (CONTRACTS.py §5)
    - Background task tracking via CampaignRun event bus

It does NOT contain any AI/LLM logic.  It is pure plumbing.

Startup:  uvicorn main_v3:app --reload --port 8000
Railway:  Change railway.toml startCommand to main_v3:app
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from CONTRACTS import (
    APIEnvelope,
    APIMeta,
    CampaignStartRequest,
    PERSONA_REGISTRY,
)
from infrastructure import init_v3_backend, shutdown_v3_backend, get_checkpointer
from infrastructure.connection import get_db_session
from logic import build_v3_graph
from models.campaign import CampaignRecord

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-30s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Campaign Run Tracker — in-memory event bus per thread_id
# ---------------------------------------------------------------------------

@dataclass
class CampaignRun:
    """Tracks a single graph execution and its emitted SSE events.

    The event bus pattern:
      - ``_run_graph`` appends (event_type, payload) tuples to ``sse_events``
        as the graph executes via ``astream_events``.
      - ``done`` is set when the graph completes (success or failure).
      - The SSE endpoint polls ``sse_events`` and yields new entries.
      - Multiple SSE clients can read the same buffer concurrently.
      - Late subscribers (after completion) replay instantly.
    """

    task: asyncio.Task
    sse_events: list[tuple[str, dict]] = field(default_factory=list)
    done: asyncio.Event = field(default_factory=asyncio.Event)
    error: Optional[str] = None


_campaign_runs: dict[str, CampaignRun] = {}
"""Maps ``thread_id → CampaignRun`` for all in-flight and recently
completed graph executions.  NOT cleared on task completion — kept
in memory so late SSE subscribers can replay events."""


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize and tear down the V3 backend."""
    report = await init_v3_backend()
    logger.info(
        "V3 Backend Health  engine=%s  pgvector=%s  tables=%s  checkpointer=%s",
        report.engine_ready,
        report.pgvector_available,
        report.tables_created,
        report.checkpointer_ready,
    )
    if report.errors:
        for err in report.errors:
            logger.warning("  ⚠ %s", err)

    # ── Compile the V3 graph with the live checkpointer ──
    checkpointer = get_checkpointer()
    compiled_graph = build_v3_graph(checkpointer=checkpointer)
    app.state.graph = compiled_graph
    logger.info(
        "V3 graph stored on app.state  checkpointer=%s",
        type(checkpointer).__name__ if checkpointer else "None",
    )

    yield

    # ── Shutdown: cancel any in-flight tasks ──
    for tid, run in list(_campaign_runs.items()):
        if not run.task.done():
            run.task.cancel()
            logger.info("Cancelled in-flight graph task  thread_id=%s", tid)
    _campaign_runs.clear()

    await shutdown_v3_backend()
    logger.info("V3 Backend shut down cleanly")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Agency V3 — Director's API",
    version="3.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS (BRIDGE_SPEC.md §6)
# ---------------------------------------------------------------------------

_allowed_origins: list[str] = [
    "http://localhost:3000",     # Vite dev server (configured port)
    "http://localhost:5173",     # Vite default fallback
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://frontend-v3-production-5ee4.up.railway.app",
]

# Railway / production frontend URL from environment
_frontend_url = os.getenv("FRONTEND_URL", "")
if _frontend_url:
    _allowed_origins.append(_frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Thread-ID", "X-Agency-Debug"],
)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/", response_model=APIEnvelope, tags=["health"])
async def root():
    """Root health check — returns a minimal APIEnvelope."""
    return APIEnvelope(
        status="success",
        data={"message": "Agency V3 is online"},
        meta=APIMeta(
            thread_id="system",
            timestamp=datetime.now(timezone.utc),
        ),
    )


# ---------------------------------------------------------------------------
# POST /campaign/start (BRIDGE_SPEC.md §2)
# ---------------------------------------------------------------------------

async def _run_graph(
    graph: Any,
    initial_state: dict[str, Any],
    thread_id: str,
) -> None:
    """Background graph execution via astream_events.

    Streams the graph and populates the CampaignRun event bus so
    SSE clients can read events in real-time or replay after
    completion.
    """
    run = _campaign_runs[thread_id]
    config = {"configurable": {"thread_id": thread_id}}

    try:
        step = 0
        async for event in graph.astream_events(
            initial_state, config=config, version="v2",
        ):
            kind = event.get("event", "")
            name = event.get("name", "")

            # ── Node start ──
            if kind == "on_chain_start" and name and name != "LangGraph":
                run.sse_events.append((
                    "node_start",
                    {"event_type": "node_start", "node_name": name},
                ))

            # ── Node end — extract logs and stage from output ──
            if kind == "on_chain_end" and name and name != "LangGraph":
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict):
                    for log_line in output.get("logs", []):
                        step += 1
                        run.sse_events.append((
                            "agent_thought",
                            {
                                "event_type": "agent_thought",
                                "text": log_line,
                                "step": step,
                            },
                        ))

                    new_stage = output.get("stage")
                    if new_stage:
                        run.sse_events.append((
                            "completion",
                            {
                                "event_type": "completion",
                                "stage": new_stage,
                                "publish_targets": output.get(
                                    "publish_targets", []
                                ),
                            },
                        ))

        # ── Check if paused for HITL ──
        state_snapshot = await graph.aget_state(config)
        if state_snapshot and state_snapshot.next:
            vals = state_snapshot.values
            run.sse_events.append((
                "breakpoint",
                {
                    "event_type": "breakpoint",
                    "breakpoint_type": "approval_required",
                    "approval_mode": vals.get("approval_mode", "active"),
                    "preview": vals.get("content"),
                }
            ))

        logger.info("Graph execution complete  thread_id=%s", thread_id)

    except Exception as e:
        logger.error(
            "Graph execution failed  thread_id=%s  error=%s",
            thread_id, e, exc_info=True,
        )
        # ── Mark campaign as failed in DB ──
        try:
            from sqlalchemy import update
            async with get_db_session() as session:
                stmt = (
                    update(CampaignRecord)
                    .where(CampaignRecord.thread_id == thread_id)
                    .values(stage="failed", updated_at=datetime.now(timezone.utc))
                )
                await session.execute(stmt)
                logger.info("Marked campaign %s as failed in database", thread_id)
        except Exception as db_err:
            logger.error("Failed to update campaign state to failed: %s", db_err)

        run.error = str(e)
        run.sse_events.append((
            "error",
            {
                "event_type": "error",
                "error_code": 500,
                "message": str(e),
                "node_name": None,
            },
        ))
    finally:
        run.done.set()


@app.post("/campaign/start", response_model=APIEnvelope, tags=["campaign"])
async def campaign_start(body: CampaignStartRequest):
    """Initialize a new campaign thread and launch the graph.

    1. Resolves the persona (from registry name or custom config).
    2. Generates a unique thread_id.
    3. Persists a CampaignRecord to PostgreSQL.
    4. Launches the LangGraph workflow as an asyncio background task.
    5. Returns the APIEnvelope with thread_id immediately (non-blocking).
    """
    # ── Resolve persona ──
    if body.persona_config:
        resolved_persona = body.persona_config
    elif body.persona_name and body.persona_name in PERSONA_REGISTRY:
        resolved_persona = PERSONA_REGISTRY[body.persona_name]
    else:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown persona '{body.persona_name}'. "
                f"Available: {list(PERSONA_REGISTRY.keys())}. "
                f"Or provide a full persona_config."
            ),
        )

    # ── Generate thread_id ──
    thread_id = str(uuid.uuid4())

    # ── Duplicate launch guard ──
    existing = _campaign_runs.get(thread_id)
    if existing and not existing.done.is_set():
        raise HTTPException(
            status_code=409,
            detail=f"Campaign {thread_id} is already running",
        )

    # ── Persist to PostgreSQL ──
    record = CampaignRecord(
        thread_id=thread_id,
        persona_name=resolved_persona.name,
        niche=body.niche,
        stage="draft",
        publish_targets=body.publish_targets,
    )

    try:
        async with get_db_session() as session:
            session.add(record)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Campaign with thread_id={thread_id} already exists",
        )

    # ── Assemble initial graph state ──
    initial_state: dict[str, Any] = {
        "messages": [{"role": "user", "content": body.niche}],
        "persona": resolved_persona,
        "content": None,
        "feedback": None,
        "retry_count": 0,
        "executive_briefing": None,
        "approval_mode": None,
        "shadow_mode": True,
        "last_error": None,
        "campaign_id": thread_id,
        "stage": "draft",
        "revision_history": [],
        "publish_targets": body.publish_targets,
        "interaction_channel": "web_ui",
        "logs": [],
    }

    # ── Launch graph as background task ──
    graph = app.state.graph
    task = asyncio.create_task(
        _run_graph(graph, initial_state, thread_id),
        name=f"graph-{thread_id[:8]}",
    )
    _campaign_runs[thread_id] = CampaignRun(task=task)

    logger.info(
        "Campaign started  thread_id=%s  persona=%s  niche=%.60s",
        thread_id, resolved_persona.name, body.niche,
    )

    return APIEnvelope(
        status="success",
        data={
            "thread_id": thread_id,
            "stage": "draft",
            "persona_name": resolved_persona.name,
            "publish_targets": body.publish_targets,
        },
        meta=APIMeta(
            thread_id=thread_id,
            timestamp=datetime.now(timezone.utc),
        ),
    )


# ---------------------------------------------------------------------------
# GET /campaign/{campaign_id}/state (BRIDGE_SPEC.md §2)
# ---------------------------------------------------------------------------

@app.get(
    "/campaign/{campaign_id}/state",
    response_model=APIEnvelope,
    tags=["campaign"],
)
async def campaign_state(campaign_id: str):
    """Retrieve the current state of a campaign by thread_id.

    Returns the CampaignRecord from the business-data table.
    Agent state (messages, revision_history) is not included here —
    it will come from the LangGraph checkpointer in a future task.
    """
    async with get_db_session() as session:
        stmt = select(CampaignRecord).where(
            CampaignRecord.thread_id == campaign_id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No campaign found with thread_id={campaign_id}",
        )

    # ── Hydrate with LangGraph pre-crash/current state ──
    graph = app.state.graph
    config = {"configurable": {"thread_id": campaign_id}}
    
    stage = record.stage
    vibe_score = record.vibe_score
    retry_count = record.retry_count
    
    try:
        state_snapshot = await graph.aget_state(config)
        if state_snapshot and state_snapshot.values:
            vals = state_snapshot.values
            if "stage" in vals and vals["stage"]:
                # Don't override 'failed' DB state if graph state says otherwise 
                # (since the DB was explicitly marked failed on crash)
                if record.stage != "failed":
                    stage = vals["stage"]
            
            if "content" in vals and vals["content"]:
                vibe_score = vals["content"].get("vibe_score", vibe_score)
                
            retry_count = vals.get("retry_count", retry_count)
    except Exception as e:
        logger.warning(
            "Could not fetch LangGraph state for campaign_id=%s: %s", 
            campaign_id, e
        )

    return APIEnvelope(
        status="success",
        data={
            "thread_id": record.thread_id,
            "persona_name": record.persona_name,
            "niche": record.niche,
            "stage": stage,
            "publish_targets": record.publish_targets,
            "vibe_score": vibe_score,
            "retry_count": retry_count,
            "created_at": (
                record.created_at.isoformat() if record.created_at else None
            ),
            "updated_at": (
                record.updated_at.isoformat() if record.updated_at else None
            ),
        },
        meta=APIMeta(
            thread_id=record.thread_id,
            timestamp=datetime.now(timezone.utc),
        ),
    )


# ---------------------------------------------------------------------------
# GET /campaign/{campaign_id}/stream (BRIDGE_SPEC.md §3 — SSE)
# ---------------------------------------------------------------------------

def _sse_frame(event_type: str, data: dict) -> str:
    """Format a single SSE frame: ``event: <type>\\ndata: <json>\\n\\n``."""
    payload = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {payload}\n\n"


@app.get("/campaign/{campaign_id}/stream", tags=["campaign"])
async def campaign_stream(campaign_id: str, request: Request):
    """Server-Sent Events stream for a running campaign.

    Reads from the in-memory CampaignRun event bus. Supports:
      - Real-time streaming (client connects while graph runs)
      - Instant replay (client connects after graph finishes)
      - Checkpoint fallback (server restarted, no in-memory data)
    """

    async def _event_generator():
        run = _campaign_runs.get(campaign_id)

        if run is not None:
            # ── Read from the in-memory event bus ──
            last_idx = 0
            while True:
                # Yield any buffered events since last read
                while last_idx < len(run.sse_events):
                    event_type, payload = run.sse_events[last_idx]
                    last_idx += 1
                    yield _sse_frame(event_type, payload)

                # If done and all events yielded, stop
                if run.done.is_set():
                    break

                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(
                        "SSE client disconnected  thread_id=%s",
                        campaign_id,
                    )
                    return

                # Poll for new events
                await asyncio.sleep(0.1)

        else:
            # ── No in-memory run — try checkpoint replay ──
            graph = app.state.graph
            config = {"configurable": {"thread_id": campaign_id}}
            try:
                state_snapshot = await graph.aget_state(config)
                if state_snapshot and state_snapshot.values:
                    vals = state_snapshot.values
                    final_stage = vals.get("stage", "draft")

                    for i, log_line in enumerate(
                        vals.get("logs", []), 1
                    ):
                        yield _sse_frame("agent_thought", {
                            "event_type": "agent_thought",
                            "text": log_line,
                            "step": i,
                        })

                    yield _sse_frame("completion", {
                        "event_type": "completion",
                        "stage": final_stage,
                        "publish_targets": vals.get(
                            "publish_targets", []
                        ),
                    })
                else:
                    yield _sse_frame("error", {
                        "event_type": "error",
                        "error_code": 404,
                        "message": (
                            f"No data found for thread_id={campaign_id}"
                        ),
                        "node_name": None,
                    })
            except Exception as e:
                logger.error(
                    "SSE checkpoint replay error  thread_id=%s  error=%s",
                    campaign_id, e, exc_info=True,
                )
                yield _sse_frame("error", {
                    "event_type": "error",
                    "error_code": 500,
                    "message": str(e),
                    "node_name": None,
                })

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-ID": campaign_id,
        },
    )
