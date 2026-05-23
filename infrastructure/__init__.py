"""
infrastructure — V3 Persistent Backend.

Owns all database connection management and LangGraph checkpointer
lifecycle for Agency V3.  This package is the sole authority for
PostgreSQL interactions in the V3 system.

Public API:
    get_db_session()        — async context manager yielding AsyncSession
    get_checkpointer()      — returns the AsyncPostgresSaver singleton
    init_v3_backend()       — startup: engine + tables + checkpointer
    shutdown_v3_backend()   — shutdown: dispose engine + close pools
"""

from infrastructure.checkpointer import get_checkpointer
from infrastructure.connection import get_db_session
from infrastructure.lifecycle import init_v3_backend, shutdown_v3_backend

__all__ = [
    "get_db_session",
    "get_checkpointer",
    "init_v3_backend",
    "shutdown_v3_backend",
]
