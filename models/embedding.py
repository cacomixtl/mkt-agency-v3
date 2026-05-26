"""
models.embedding — V3 Conversation Embedding ORM model.

Stores vector embeddings of agent node outputs for semantic retrieval
(RAG).  Each row represents a single embedded text fragment produced
by a specific graph node within a campaign thread.

The pgvector extension must be enabled (handled by lifecycle.py).

Contract compliance (CONTRACTS.py cross-reference):
    thread_id     → EmbeddingMeta.thread_id / APIMeta.thread_id
    node_name     → EmbeddingMeta.node_name
    persona_name  → EmbeddingMeta.persona_name
    niche         → EmbeddingMeta.niche
    stage         → EmbeddingMeta.stage / CampaignStage

Migration Impact: New table — created by metadata.create_all().
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from models.campaign import Base

# ---------------------------------------------------------------------------
# Embedding dimensions — must match the chosen embedding model.
# Google text-embedding-004 produces 768-dimensional vectors.
# ---------------------------------------------------------------------------

EMBEDDING_DIM = 768


# ---------------------------------------------------------------------------
# ConversationEmbedding
# ---------------------------------------------------------------------------


class ConversationEmbedding(Base):
    """Durable vector embedding of a single agent node output.

    One row per (thread_id, node_name, content) triple.  The content_hash
    column enables idempotent writes — re-embedding the same text for the
    same node in the same thread is a no-op.
    """

    __tablename__ = "conversation_embeddings"

    id: uuid.UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    thread_id: str = Column(
        String(64),
        nullable=False,
        index=True,
        comment="LangGraph thread identifier — scopes retrieval to a user",
    )
    node_name: str = Column(
        String(64),
        nullable=False,
        comment="Graph node that produced this text (e.g. 'creative_worker')",
    )
    content: str = Column(
        Text,
        nullable=False,
        comment="Raw text that was embedded",
    )
    content_hash: str = Column(
        String(64),
        nullable=False,
        comment="SHA-256 of content — used for idempotent upsert",
    )
    embedding = Column(
        Vector(EMBEDDING_DIM),
        nullable=False,
        comment=f"pgvector column ({EMBEDDING_DIM}-dim, text-embedding-004)",
    )
    persona_name: str = Column(
        String(128),
        nullable=False,
        default="",
        server_default="",
        comment="Persona name at time of embedding",
    )
    niche: str = Column(
        Text,
        nullable=False,
        default="",
        server_default="",
        comment="Business/product brief for this thread",
    )
    stage: str = Column(
        String(32),
        nullable=True,
        default=None,
        comment="Campaign stage when embedding was created",
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    # Composite unique constraint for idempotent writes:
    # same thread + same node + same content = same row
    __table_args__ = (
        Index(
            "uq_embedding_thread_node_hash",
            "thread_id",
            "node_name",
            "content_hash",
            unique=True,
        ),
    )

    @staticmethod
    def hash_content(content: str) -> str:
        """Produce a deterministic SHA-256 hex digest of the content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:
        return (
            f"<ConversationEmbedding id={str(self.id):.8} "
            f"thread={self.thread_id} "
            f"node={self.node_name}>"
        )
