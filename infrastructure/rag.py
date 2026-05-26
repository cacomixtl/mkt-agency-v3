"""
infrastructure.rag — RAG Embedding Storage & Retrieval.

Provides the embedding pipeline for Agency V3's semantic memory:
    - embed_text()       — generate a vector from text via Google text-embedding-004
    - store_embedding()  — embed text and write to PostgreSQL + pgvector
    - search_similar()   — retrieve semantically similar embeddings (tenant-scoped)

This module uses the SQLAlchemy async pool (not the psycopg3 checkpointer pool).
pgvector operations are handled via the ``pgvector`` SQLAlchemy integration.

Environment:
    GOOGLE_API_KEY — required for the embedding model

Migration Impact: None (uses existing tables created by lifecycle.py).
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from infrastructure.connection import get_db_session
from models.embedding import EMBEDDING_DIM, ConversationEmbedding

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedding model (lazy-initialized singleton)
# ---------------------------------------------------------------------------

_embeddings_model = None


def _get_embeddings_model():
    """Return the Google embedding model, initializing on first call.

    Raises RuntimeError if GOOGLE_API_KEY is not set.
    """
    global _embeddings_model
    if _embeddings_model is not None:
        return _embeddings_model

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set — cannot initialize embedding model. "
            "Set it in .env or as an environment variable."
        )

    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    _embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key,
    )
    logger.info(
        "Embedding model initialized: text-embedding-004 (%d dims)", EMBEDDING_DIM
    )
    return _embeddings_model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def embed_text(text_content: str) -> list[float]:
    """Generate a vector embedding for the given text.

    Uses Google's text-embedding-004 model (768 dimensions).

    Args:
        text_content: The text to embed.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        RuntimeError: If GOOGLE_API_KEY is not set.
    """
    model = _get_embeddings_model()
    vector = await model.aembed_query(text_content)
    return vector


async def store_embedding(
    *,
    thread_id: str,
    node_name: str,
    content: str,
    persona_name: str = "",
    niche: str = "",
    stage: Optional[str] = None,
) -> uuid.UUID:
    """Embed text and write it to the conversation_embeddings table.

    This operation is idempotent — storing the same (thread_id, node_name,
    content) triple a second time will not create a duplicate row.

    Args:
        thread_id: LangGraph thread identifier.
        node_name: The graph node that produced this text.
        content: The raw text to embed.
        persona_name: Persona name at time of embedding.
        niche: Business/product brief for this thread.
        stage: Campaign stage when embedding was created.

    Returns:
        The UUID of the stored (or existing) embedding row.

    Raises:
        RuntimeError: If GOOGLE_API_KEY or DATABASE_URL is not set.
    """
    # Generate embedding vector
    vector = await embed_text(content)

    # Compute content hash for idempotency
    content_hash = ConversationEmbedding.hash_content(content)
    row_id = uuid.uuid4()

    # Upsert: insert if new, skip if (thread_id, node_name, content_hash) exists
    stmt = pg_insert(ConversationEmbedding).values(
        id=row_id,
        thread_id=thread_id,
        node_name=node_name,
        content=content,
        content_hash=content_hash,
        embedding=vector,
        persona_name=persona_name,
        niche=niche,
        stage=stage,
    )
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["thread_id", "node_name", "content_hash"],
    )

    async with get_db_session() as session:
        result = await session.execute(stmt)

        if result.rowcount == 0:
            # Row already existed — fetch its ID
            existing = await session.execute(
                select(ConversationEmbedding.id).where(
                    ConversationEmbedding.thread_id == thread_id,
                    ConversationEmbedding.node_name == node_name,
                    ConversationEmbedding.content_hash == content_hash,
                )
            )
            row_id = existing.scalar_one()
            logger.debug(
                "Embedding already exists  thread=%s  node=%s  id=%s",
                thread_id,
                node_name,
                row_id,
            )
        else:
            logger.info(
                "Stored embedding  thread=%s  node=%s  id=%s  dim=%d",
                thread_id,
                node_name,
                row_id,
                len(vector),
            )

    return row_id


async def search_similar(
    *,
    query: str,
    thread_id: str,
    top_k: int = 5,
) -> list[ConversationEmbedding]:
    """Retrieve the most semantically similar embeddings for a given thread.

    Uses cosine distance via pgvector's ``<=>`` operator.  Results are
    scoped to a single thread_id (tenant-scoped retrieval).

    Args:
        query: The search query text (will be embedded).
        thread_id: Scope results to this thread only.
        top_k: Maximum number of results to return.

    Returns:
        A list of ConversationEmbedding rows, ordered by similarity
        (most similar first).
    """
    query_vector = await embed_text(query)

    async with get_db_session() as session:
        # pgvector cosine distance: embedding <=> query_vector
        # Lower distance = more similar
        stmt = (
            select(ConversationEmbedding)
            .where(ConversationEmbedding.thread_id == thread_id)
            .order_by(
                ConversationEmbedding.embedding.cosine_distance(query_vector)
            )
            .limit(top_k)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()

    logger.debug(
        "search_similar  thread=%s  query=%.40s  results=%d",
        thread_id,
        query,
        len(rows),
    )
    return list(rows)


async def search_similar_global(
    *,
    query: str,
    top_k: int = 5,
) -> list[ConversationEmbedding]:
    """Retrieve the most semantically similar embeddings across ALL threads.

    This is the global (unscoped) search path — intended for future BI
    and cross-campaign analysis, NOT for user-facing retrieval.

    Args:
        query: The search query text (will be embedded).
        top_k: Maximum number of results to return.

    Returns:
        A list of ConversationEmbedding rows, ordered by similarity.
    """
    query_vector = await embed_text(query)

    async with get_db_session() as session:
        stmt = (
            select(ConversationEmbedding)
            .order_by(
                ConversationEmbedding.embedding.cosine_distance(query_vector)
            )
            .limit(top_k)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()

    logger.debug(
        "search_similar_global  query=%.40s  results=%d",
        query,
        len(rows),
    )
    return list(rows)
