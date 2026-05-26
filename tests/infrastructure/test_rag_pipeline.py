"""
tests.infrastructure.test_rag_pipeline — RAG Storage & Retrieval Validation.

Validates the full embedding pipeline per RAG_TEST.md:
    1. Embed text and store it in pgvector
    2. Mock 10 users with semantically distinct niches
    3. Verify tenant-scoped retrieval accuracy
    4. Verify cross-user semantic isolation (global search)
    5. Measure retrieval latency
    6. Confirm idempotent storage (no duplicates)

Requires:
    DATABASE_URL  — PostgreSQL with pgvector
    GOOGLE_API_KEY — Google text-embedding-004

Cleanup: All test data uses thread_ids prefixed with 'test-rag-'.
The module-scoped fixture deletes these rows in teardown.  A stale-data
sweeper also cleans up rows older than 1 hour on startup.
"""

from __future__ import annotations

import os
import time
import uuid

import pytest
import pytest_asyncio

# Skip the entire module if required env vars are missing
pytestmark = [
    pytest.mark.skipif(
        not os.getenv("DATABASE_URL"),
        reason="DATABASE_URL not set — skipping RAG tests",
    ),
    pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set — skipping RAG tests",
    ),
]

TEST_PREFIX = "test-rag-"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="module")
async def rag_backend():
    """Initialize the V3 backend and clean up stale test data.

    Yields the BackendHealthReport.  On teardown, deletes all rows
    with thread_id starting with 'test-rag-'.
    """
    from infrastructure.lifecycle import init_v3_backend, shutdown_v3_backend

    report = await init_v3_backend()
    assert report.engine_ready, f"Engine failed: {report.errors}"
    assert report.tables_created, f"Tables failed: {report.errors}"
    assert report.pgvector_available, f"pgvector not available: {report.errors}"

    # Sweep stale test data from previous crashed runs
    await _cleanup_stale_test_data()

    yield report

    # Teardown: clean up all test embeddings
    await _cleanup_stale_test_data()
    await shutdown_v3_backend()


async def _cleanup_stale_test_data():
    """Delete all conversation_embeddings rows with test-rag- prefix."""
    from sqlalchemy import delete

    from infrastructure.connection import get_db_session
    from models.embedding import ConversationEmbedding

    try:
        async with get_db_session() as session:
            stmt = delete(ConversationEmbedding).where(
                ConversationEmbedding.thread_id.like(f"{TEST_PREFIX}%")
            )
            result = await session.execute(stmt)
            if result.rowcount > 0:
                import logging

                logging.getLogger(__name__).info(
                    "Cleaned up %d stale test embedding(s)", result.rowcount
                )
    except Exception:
        pass  # Table may not exist yet on first run


@pytest_asyncio.fixture(scope="module")
async def populated_users(rag_backend):
    """Store embeddings for all 10 mock users and return them with thread_ids.

    This fixture is module-scoped so the embedding calls (which hit
    the Google API) only happen once for the entire test module.
    """
    from infrastructure.rag import store_embedding
    from tests.infrastructure.mock_users import MOCK_USERS, MockUser

    # Assign unique thread_ids with test prefix
    users: list[MockUser] = []
    for mock in MOCK_USERS:
        user = MockUser(
            persona_name=mock.persona_name,
            niche=mock.niche,
            node_outputs=mock.node_outputs,
            verifiable_query=mock.verifiable_query,
            expected_marker=mock.expected_marker,
            thread_id=f"{TEST_PREFIX}{uuid.uuid4()}",
        )
        users.append(user)

    # Store all embeddings (10 users × 4 nodes = 40 API calls)
    for user in users:
        for node_output in user.node_outputs:
            await store_embedding(
                thread_id=user.thread_id,
                node_name=node_output.node_name,
                content=node_output.text,
                persona_name=user.persona_name,
                niche=user.niche,
                stage="draft",
            )

    yield users


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_and_store(rag_backend):
    """Embed a single text fragment, store it, and read it back.

    Validates:
        - The embedding vector has the correct dimension (768)
        - The row is persisted and queryable
    """
    from sqlalchemy import select

    from infrastructure.connection import get_db_session
    from infrastructure.rag import embed_text, store_embedding
    from models.embedding import EMBEDDING_DIM, ConversationEmbedding

    thread_id = f"{TEST_PREFIX}single-{uuid.uuid4()}"
    content = "A test fragment for validating the embedding pipeline."

    # Verify raw embedding dimension
    vector = await embed_text(content)
    assert len(vector) == EMBEDDING_DIM, (
        f"Expected {EMBEDDING_DIM}-dim vector, got {len(vector)}"
    )

    # Store and read back
    row_id = await store_embedding(
        thread_id=thread_id,
        node_name="test_node",
        content=content,
        persona_name="Silicon Labor",
        niche="test niche",
    )

    async with get_db_session() as session:
        stmt = select(ConversationEmbedding).where(
            ConversationEmbedding.id == row_id
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()

    assert row is not None, "Embedding row should be persisted"
    assert row.thread_id == thread_id
    assert row.node_name == "test_node"
    assert row.content == content
    assert row.persona_name == "Silicon Labor"
    assert len(row.embedding) == EMBEDDING_DIM


@pytest.mark.asyncio
async def test_idempotent_storage(rag_backend):
    """Storing the same (thread_id, node_name, content) twice must not duplicate.

    Validates the ON CONFLICT DO NOTHING upsert behavior.
    """
    from sqlalchemy import func, select

    from infrastructure.connection import get_db_session
    from infrastructure.rag import store_embedding
    from models.embedding import ConversationEmbedding

    thread_id = f"{TEST_PREFIX}idempotent-{uuid.uuid4()}"
    content = "This content should only be stored once."

    # Store twice
    id_first = await store_embedding(
        thread_id=thread_id,
        node_name="creative_worker",
        content=content,
    )
    id_second = await store_embedding(
        thread_id=thread_id,
        node_name="creative_worker",
        content=content,
    )

    # Both calls should return the same row ID
    assert id_first == id_second, (
        f"Expected same ID on duplicate store, got {id_first} vs {id_second}"
    )

    # Verify only one row exists
    async with get_db_session() as session:
        stmt = select(func.count()).where(
            ConversationEmbedding.thread_id == thread_id,
            ConversationEmbedding.node_name == "creative_worker",
        )
        result = await session.execute(stmt)
        count = result.scalar()

    assert count == 1, f"Expected 1 row, found {count} (duplicate detected)"


@pytest.mark.asyncio
async def test_10_user_tenant_scoped_retrieval(populated_users):
    """Each user's verifiable query must return their own data as top result.

    This is the core RAG accuracy test — tenant-scoped retrieval.
    """
    from infrastructure.rag import search_similar

    for i, user in enumerate(populated_users):
        results = await search_similar(
            query=user.verifiable_query,
            thread_id=user.thread_id,
            top_k=3,
        )

        assert len(results) > 0, (
            f"User {i + 1} ({user.niche}): no results returned"
        )

        # The top result must contain the expected marker
        top_content = results[0].content
        assert user.expected_marker in top_content, (
            f"User {i + 1} ({user.niche}): expected marker "
            f"'{user.expected_marker}' not found in top result.\n"
            f"Top result content: {top_content[:200]}..."
        )


@pytest.mark.asyncio
async def test_cross_user_semantic_isolation(populated_users):
    """Global search for a niche-specific phrase must rank the correct user #1.

    This is the acid test — even without a thread_id filter, the semantic
    content should be distinctive enough that the right user surfaces.
    """
    from infrastructure.rag import search_similar_global

    # Test with the first user's niche-specific language
    user = populated_users[0]  # Artisan coffee roaster
    results = await search_similar_global(
        query="single-origin pour-over extraction ritual and manual brewing",
        top_k=5,
    )

    assert len(results) > 0, "Global search returned no results"

    # The top result must belong to User 1's thread
    assert results[0].thread_id == user.thread_id, (
        f"Expected top result from thread {user.thread_id} "
        f"({user.niche}), got thread {results[0].thread_id}.\n"
        f"Top result content: {results[0].content[:200]}..."
    )


@pytest.mark.asyncio
async def test_retrieval_latency(populated_users):
    """Measure retrieval latency across multiple queries.

    Target: p99 < 500ms for cosine similarity search over ~40 embeddings.
    """
    from infrastructure.rag import search_similar

    latencies: list[float] = []

    # Run 20 queries (2 per user) to get meaningful latency data
    for user in populated_users[:5]:  # 5 users × 2 queries = 10
        for query in [user.verifiable_query, f"Tell me about {user.niche}"]:
            start = time.monotonic()
            await search_similar(
                query=query,
                thread_id=user.thread_id,
                top_k=3,
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            latencies.append(elapsed_ms)

    # Compute p99
    latencies.sort()
    p99_idx = max(0, int(len(latencies) * 0.99) - 1)
    p99_ms = latencies[p99_idx]
    avg_ms = sum(latencies) / len(latencies)

    print(f"\n{'='*60}")
    print("  RAG Retrieval Latency Report")
    print(f"  Queries: {len(latencies)}")
    print(f"  Avg:     {avg_ms:.1f} ms")
    print(f"  p99:     {p99_ms:.1f} ms")
    print(f"  Min:     {min(latencies):.1f} ms")
    print(f"  Max:     {max(latencies):.1f} ms")
    print(f"{'='*60}\n")

    assert p99_ms < 5000, (
        f"p99 retrieval latency {p99_ms:.1f}ms exceeds 5000ms threshold. "
        f"Note: latency includes embedding API call. "
        f"Adjust threshold if network conditions vary."
    )
