"""
Test script to audit the pgvector capabilities of the ConversationChunk table.
Run this script to ensure semantic search is working correctly:
`python tests/test_vector_db.py`
"""

import asyncio

from dotenv import load_dotenv

# Ensure we load env vars before importing app modules
load_dotenv()

from app.core.database import get_session
from app.models.conversation import ConversationChunk
from app.services.agent.service import _get_embedding
from sqlmodel import select


async def audit_vector_db():
    print("--- Starting pgvector Audit ---")

    # 1. Provide a test query
    test_query = "Quiero promocionar mi nueva mezcla de café de especialidad"
    print(f"\n[1] Generating embedding for test query: '{test_query}'")

    try:
        query_embedding = await _get_embedding(test_query)
        print(f"✅ Generated embedding of length {len(query_embedding)}")
    except Exception as e:
        print(f"❌ Failed to generate embedding: {e}")
        return

    # 2. Perform vector search in the DB using Cosine Distance
    print("\n[2] Searching Database (ConversationChunks) for nearest neighbors...")
    try:
        async with get_session() as session:
            # Vector cosine distance is <-> in pgvector
            # The smaller the distance, the closer the match
            stmt = (
                select(ConversationChunk)
                .order_by(ConversationChunk.embedding.cosine_distance(query_embedding))
                .limit(3)
            )

            result = await session.exec(stmt)
            chunks = result.all()

            if not chunks:
                print(
                    "⚠️ No conversation chunks found in the database. Send some messages to the bot first!"
                )
                return

            print(f"✅ Found {len(chunks)} closest chunks:\n")
            for i, chunk in enumerate(chunks, 1):
                # We can calculate the raw distance if we want, but pgvector orders them implicitly
                print(f"--- Neighborhood Rank #{i} ---")
                print(f"Phone: {chunk.user_phone}")
                print(f"Role: {chunk.role}")
                print(f"Content: {chunk.content[:150]}...")
                print("----------------------------\n")

    except Exception as e:
        print(
            f"❌ Database search failed. Are you sure pgvector is enabled? Error: {e}"
        )


if __name__ == "__main__":
    asyncio.run(audit_vector_db())
