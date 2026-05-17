"""
infrastructure.checkpointer — LangGraph AsyncPostgresSaver lifecycle.

Manages a dedicated ``psycopg_pool.AsyncConnectionPool`` for the
LangGraph checkpointer.  This pool is SEPARATE from the SQLAlchemy
asyncpg pool used for business-data tables — they coexist on the
same PostgreSQL instance but use different driver stacks.

Tables created by ``AsyncPostgresSaver.setup()``:
    - checkpoints
    - checkpoint_writes
    - checkpoint_blobs

These tables are idempotent — calling setup() multiple times is safe.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from infrastructure.connection import _normalize_psycopg_url

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_checkpointer: Optional[object] = None
_pool: Optional[object] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def init_checkpointer() -> bool:
    """Initialize the AsyncPostgresSaver and its connection pool.

    Creates the LangGraph checkpoint tables on first call (idempotent).

    Returns:
        True if the checkpointer is ready, False if DATABASE_URL is
        missing or initialization failed.
    """
    global _checkpointer, _pool

    if _checkpointer is not None:
        return True

    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        logger.warning("DATABASE_URL not set — LangGraph checkpointer disabled")
        return False

    psycopg_url = _normalize_psycopg_url(raw_url)

    try:
        from psycopg_pool import AsyncConnectionPool
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        _pool = AsyncConnectionPool(
            conninfo=psycopg_url,
            min_size=1,
            max_size=5,
            open=False,
            # langgraph's setup() runs CREATE INDEX CONCURRENTLY which
            # cannot execute inside a transaction block.  autocommit=True
            # matches the kwargs used by AsyncPostgresSaver.from_conn_string().
            kwargs={"autocommit": True, "prepare_threshold": 0},
        )
        await _pool.open()

        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()

        logger.info("LangGraph AsyncPostgresSaver initialized (tables created/verified)")
        return True

    except Exception as e:
        logger.error("Failed to initialize LangGraph checkpointer: %s", e, exc_info=True)
        _checkpointer = None
        _pool = None
        return False


def get_checkpointer():
    """Return the AsyncPostgresSaver singleton.

    Returns None if the checkpointer has not been initialized or
    initialization failed.
    """
    return _checkpointer


async def shutdown_checkpointer() -> None:
    """Close the psycopg connection pool cleanly."""
    global _checkpointer, _pool

    if _pool is not None:
        try:
            await _pool.close()
            logger.info("LangGraph checkpointer pool closed")
        except Exception as e:
            logger.warning("Error closing checkpointer pool: %s", e)
        finally:
            _pool = None
            _checkpointer = None
