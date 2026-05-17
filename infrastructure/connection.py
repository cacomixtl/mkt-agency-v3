"""
infrastructure.connection — Async PostgreSQL connection management.

Provides the SQLAlchemy 2.0 async engine and session factory for
V3 business-data tables (CampaignRecord, etc.).

The LangGraph checkpointer uses its own psycopg pool (see checkpointer.py).
This module handles the asyncpg pool exclusively.

Connection URL normalization:
    Railway provides  → postgres://user:pass@host:port/db
    asyncpg needs     → postgresql+asyncpg://user:pass@host:port/db
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load .env so os.getenv() picks up DATABASE_URL and pool tuning knobs
load_dotenv()
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

def _normalize_asyncpg_url(raw: str) -> str:
    """Convert a raw DATABASE_URL to asyncpg format.

    Handles the three common variants:
        postgres://        → postgresql+asyncpg://
        postgresql://      → postgresql+asyncpg://
        postgresql+asyncpg:// → pass-through
    """
    if raw.startswith("postgresql+asyncpg://"):
        return raw
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+asyncpg://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return f"postgresql+asyncpg://{raw}"


def _normalize_psycopg_url(raw: str) -> str:
    """Convert a raw DATABASE_URL to psycopg3 format.

    psycopg3 expects plain ``postgresql://`` — NOT the SQLAlchemy
    ``+asyncpg`` dialect prefix.
    """
    if raw.startswith("postgresql+asyncpg://"):
        return raw.replace("postgresql+asyncpg://", "postgresql://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql://", 1)
    if raw.startswith("postgresql://"):
        return raw
    return f"postgresql://{raw}"


# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

def _get_database_url() -> Optional[str]:
    """Read DATABASE_URL from the environment (never hardcoded)."""
    return os.getenv("DATABASE_URL")


def get_engine() -> AsyncEngine:
    """Return the singleton AsyncEngine, creating it on first call.

    Raises RuntimeError if DATABASE_URL is not set.
    """
    global _engine
    if _engine is not None:
        return _engine

    raw_url = _get_database_url()
    if not raw_url:
        raise RuntimeError(
            "DATABASE_URL is not set — cannot create async engine. "
            "Set it in .env or as an environment variable."
        )

    pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    _engine = create_async_engine(
        _normalize_asyncpg_url(raw_url),
        echo=os.getenv("DB_ECHO", "").lower() in ("1", "true", "yes"),
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_pre_ping=True,
    )
    logger.info(
        "AsyncEngine created  (pool_size=%d, max_overflow=%d, pool_pre_ping=True)",
        pool_size,
        max_overflow,
    )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the singleton async session factory."""
    global _session_factory
    if _session_factory is not None:
        return _session_factory

    _session_factory = async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async session.

    Usage::

        async with get_db_session() as session:
            session.add(record)
            # auto-commit on clean exit, auto-rollback on exception
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Teardown
# ---------------------------------------------------------------------------

async def dispose_engine() -> None:
    """Dispose of the async engine and release all pooled connections."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("AsyncEngine disposed")
        _engine = None
        _session_factory = None
