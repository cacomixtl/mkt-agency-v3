"""
infrastructure.lifecycle — Startup and shutdown orchestration.

Aggregates engine initialization, table creation, pgvector extension,
and checkpointer setup into two clean functions called from the
FastAPI lifespan.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from infrastructure.checkpointer import init_checkpointer, shutdown_checkpointer
from infrastructure.connection import dispose_engine, get_engine

logger = logging.getLogger(__name__)


@dataclass
class BackendHealthReport:
    """Structured report returned by init_v3_backend()."""

    engine_ready: bool = False
    pgvector_available: bool = False
    tables_created: bool = False
    checkpointer_ready: bool = False
    errors: list[str] = field(default_factory=list)


async def init_v3_backend() -> BackendHealthReport:
    """Initialize the entire V3 persistent backend.

    1. Create the async engine (validates DATABASE_URL).
    2. Enable pgvector extension (non-fatal if unavailable).
    3. Create V3 business-data tables via metadata.create_all().
    4. Initialize the LangGraph checkpointer.

    Returns a BackendHealthReport so the caller can log/expose health.
    """
    report = BackendHealthReport()

    # ── 1. Engine ──
    try:
        engine = get_engine()
        report.engine_ready = True
    except RuntimeError as e:
        report.errors.append(f"Engine: {e}")
        logger.error("Failed to create async engine: %s", e)
        return report

    # ── 2. pgvector extension ──
    try:
        from sqlalchemy import text

        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        report.pgvector_available = True
        logger.info("pgvector extension enabled")
    except Exception as e:
        report.errors.append(f"pgvector: {e}")
        logger.warning(
            "pgvector extension not available — vector features disabled. Error: %s", e
        )

    # ── 3. Create V3 tables ──
    try:
        # Import the V3 Base so metadata knows about our models
        from models.campaign import Base  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        report.tables_created = True
        logger.info("V3 business-data tables created/verified")
    except Exception as e:
        report.errors.append(f"Tables: {e}")
        logger.error("Failed to create V3 tables: %s", e, exc_info=True)

    # ── 4. Checkpointer ──
    checkpointer_ok = await init_checkpointer()
    report.checkpointer_ready = checkpointer_ok
    if not checkpointer_ok:
        report.errors.append("Checkpointer: initialization failed (see logs)")

    # ── Summary ──
    logger.info(
        "V3 backend initialized  (engine=%s, pgvector=%s, tables=%s, checkpointer=%s)",
        report.engine_ready,
        report.pgvector_available,
        report.tables_created,
        report.checkpointer_ready,
    )
    return report


async def shutdown_v3_backend() -> None:
    """Gracefully shut down all V3 backend resources."""
    await shutdown_checkpointer()
    await dispose_engine()
    logger.info("V3 backend shut down")
