"""
models — V3 Business-Data ORM models.

These models represent durable business records stored in PostgreSQL.
They are strictly separated from LangGraph agent state (which lives
in the checkpointer tables).

All fields must align with the Pydantic models in CONTRACTS.py.
"""

from models.campaign import CampaignRecord
from models.embedding import ConversationEmbedding

__all__ = ["CampaignRecord", "ConversationEmbedding"]
