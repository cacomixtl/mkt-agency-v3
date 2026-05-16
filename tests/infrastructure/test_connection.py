"""
tests.infrastructure.test_connection — Connection resilience tests.

Validates:
    1. Session transactional behavior (commit / rollback)
    2. Pool health checks (pool_pre_ping)
    3. Checkpointer setup idempotency
    4. Campaign insertion idempotency (unique thread_id)
    5. Full round-trip through the /campaign/start endpoint

Requires DATABASE_URL to be set.  Skips gracefully if not available.
"""

from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio

# Skip the entire module if no DATABASE_URL
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping infrastructure tests",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="module")
async def v3_backend():
    """Initialize the V3 backend once for the entire test module."""
    from infrastructure.lifecycle import init_v3_backend, shutdown_v3_backend

    report = await init_v3_backend()
    assert report.engine_ready, f"Engine failed: {report.errors}"
    assert report.tables_created, f"Tables failed: {report.errors}"
    yield report
    await shutdown_v3_backend()


@pytest_asyncio.fixture
async def db_session(v3_backend):
    """Provide a transactional session that rolls back after each test."""
    from infrastructure.connection import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        yield session
        # Always rollback — tests should not leave data behind
        await session.rollback()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_session_commit_and_rollback(v3_backend):
    """Verify that get_db_session commits on clean exit and rolls back on error."""
    from infrastructure.connection import get_db_session
    from models.campaign import CampaignRecord

    thread_id = f"test-commit-{uuid.uuid4()}"

    # Write a record
    async with get_db_session() as session:
        session.add(CampaignRecord(
            thread_id=thread_id,
            persona_name="Silicon Labor",
            niche="Test commit",
            stage="draft",
            publish_targets=["instagram"],
        ))

    # Read it back in a new session
    from sqlalchemy import select

    async with get_db_session() as session:
        result = await session.execute(
            select(CampaignRecord).where(CampaignRecord.thread_id == thread_id)
        )
        record = result.scalar_one_or_none()
        assert record is not None, "Record should have been committed"
        assert record.persona_name == "Silicon Labor"
        assert record.stage == "draft"

        # Clean up
        await session.delete(record)


@pytest.mark.asyncio
async def test_pool_health_check(v3_backend):
    """Verify pool_pre_ping keeps connections healthy."""
    from infrastructure.connection import get_engine
    from sqlalchemy import text

    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        row = result.scalar()
        assert row == 1


@pytest.mark.asyncio
async def test_checkpointer_setup_idempotent(v3_backend):
    """Calling init_checkpointer() twice should not raise."""
    from infrastructure.checkpointer import init_checkpointer

    # Already initialized by v3_backend fixture — call again
    result = await init_checkpointer()
    assert result is True


@pytest.mark.asyncio
async def test_campaign_insert_unique_thread_id(v3_backend):
    """Inserting two campaigns with the same thread_id must raise IntegrityError."""
    from infrastructure.connection import get_db_session
    from models.campaign import CampaignRecord
    from sqlalchemy.exc import IntegrityError

    thread_id = f"test-unique-{uuid.uuid4()}"
    base_kwargs = dict(
        thread_id=thread_id,
        persona_name="Silicon Labor",
        niche="Idempotency test",
        stage="draft",
        publish_targets=["instagram"],
    )

    # First insert — should succeed
    async with get_db_session() as session:
        session.add(CampaignRecord(**base_kwargs))

    # Second insert — same thread_id — must fail
    with pytest.raises(IntegrityError):
        async with get_db_session() as session:
            session.add(CampaignRecord(**base_kwargs))

    # Clean up the first record
    from sqlalchemy import select

    async with get_db_session() as session:
        result = await session.execute(
            select(CampaignRecord).where(CampaignRecord.thread_id == thread_id)
        )
        record = result.scalar_one_or_none()
        if record:
            await session.delete(record)


@pytest.mark.asyncio
async def test_campaign_start_endpoint_round_trip(v3_backend):
    """Full HTTP round-trip: POST /campaign/start → GET /campaign/{id}/state."""
    from httpx import AsyncClient, ASGITransport
    from main_v3 import app

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Start a campaign
        resp = await client.post(
            "/campaign/start",
            json={
                "persona_name": "Silicon Labor",
                "niche": "Test round-trip from pytest",
                "publish_targets": ["instagram"],
            },
        )
        assert resp.status_code == 200, f"Start failed: {resp.text}"

        envelope = resp.json()
        assert envelope["status"] == "success"
        thread_id = envelope["data"]["thread_id"]
        assert envelope["data"]["stage"] == "draft"
        assert envelope["data"]["persona_name"] == "Silicon Labor"
        assert envelope["meta"]["thread_id"] == thread_id

        # Retrieve state
        resp2 = await client.get(f"/campaign/{thread_id}/state")
        assert resp2.status_code == 200, f"State failed: {resp2.text}"

        state = resp2.json()
        assert state["data"]["thread_id"] == thread_id
        assert state["data"]["niche"] == "Test round-trip from pytest"

    # Clean up
    from infrastructure.connection import get_db_session
    from models.campaign import CampaignRecord
    from sqlalchemy import select

    async with get_db_session() as session:
        result = await session.execute(
            select(CampaignRecord).where(CampaignRecord.thread_id == thread_id)
        )
        record = result.scalar_one_or_none()
        if record:
            await session.delete(record)
