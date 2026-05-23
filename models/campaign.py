"""
models.campaign — V3 CampaignRecord ORM model.

Stores business-data for each campaign thread.  This is the "identity
card" of a campaign — who started it, what persona, what stage.

Agent state (messages, revision_history, content artifacts) is NOT
stored here.  It lives exclusively in the LangGraph checkpoint tables
managed by AsyncPostgresSaver.

┌──────────────────────────────────────────────────────────────────┐
│  ALPHA-PHASE WARNING                                            │
│                                                                 │
│  We use metadata.create_all() — NOT Alembic migrations.         │
│  If CONTRACTS.py requires a schema change to this model,        │
│  the Director must be notified.  The table will need to be      │
│  manually DROPped and re-created.                               │
└──────────────────────────────────────────────────────────────────┘

Contract compliance (CONTRACTS.py cross-reference):
    thread_id       → APIMeta.thread_id
    persona_name    → CampaignStartRequest.persona_name
    niche           → CampaignStartRequest.niche
    stage           → CampaignStage (V3AgencyState.stage)
    publish_targets → CampaignStartRequest.publish_targets
    vibe_score      → MarketingContent.vibe_score
    retry_count     → V3AgencyState.retry_count
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# Declarative Base for V3 models
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Base class for all V3 ORM models.

    Uses its own metadata — completely independent from the V1
    SQLModel metadata in app/models/.
    """

    pass


# ---------------------------------------------------------------------------
# CampaignRecord
# ---------------------------------------------------------------------------


class CampaignRecord(Base):
    """Durable business-data record for a single campaign thread.

    One row per campaign.  The ``thread_id`` is the foreign key into
    LangGraph's checkpoint tables (managed separately).
    """

    __tablename__ = "campaign_records"

    id: uuid.UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    thread_id: str = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="LangGraph thread identifier — links to checkpoint tables",
    )
    persona_name: str = Column(
        String(128),
        nullable=False,
        comment="Resolved persona name from CampaignStartRequest",
    )
    niche: str = Column(
        Text,
        nullable=False,
        comment="Business/product brief from CampaignStartRequest",
    )
    stage: str = Column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
        comment="Mirrors CampaignStage from CONTRACTS.py",
    )
    publish_targets: list = Column(
        JSON,
        nullable=False,
        default=["instagram"],
        server_default='["instagram"]',
        comment="Target platforms from CampaignStartRequest",
    )
    vibe_score: float | None = Column(
        Float,
        nullable=True,
        default=None,
        comment="Critic vibe_score — updated by graph callbacks",
    )
    retry_count: int = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Revision loop count — updated by graph callbacks",
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<CampaignRecord id={self.id!s:.8} "
            f"thread={self.thread_id} "
            f"stage={self.stage} "
            f"persona={self.persona_name}>"
        )
