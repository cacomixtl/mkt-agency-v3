"""
logic.nodes.creative — Creative Worker Node.

Generates marketing content (caption + image prompt) driven by the
dynamically injected ``PersonaConfig``. Wrapped with resilience layers
and output validation.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from CONTRACTS import MarketingContent
from guardrails import resilient_call, validate_node_output

logger = logging.getLogger(__name__)

_CREATIVE_SYSTEM_PROMPT = """You are an elite Marketing Copywriter and Art Director.
Generate a social media campaign adhering strictly to the Brand Context below.

BRAND CONTEXT:
Tone & Voice: {tone}
Visual Aesthetic: {visuals}
Brand Philosophy: {philosophy}
Forbidden Terms (NEVER use these): {forbidden_terms}

INSTRUCTIONS:
1. Return a structured MarketingContent object.
2. The `caption` MUST embody the specified Tone & Voice and Brand Philosophy.
3. The `caption` MUST NOT contain any Forbidden Terms or Emojis.
4. The `image_prompt` MUST embody the Visual Aesthetic explicitly.
5. Provide a raw, unadorned string for both (no markdown quotes).
"""

_CREATIVE_USER_PROMPT = """USER BRIEF:
{niche}

JUDGE FEEDBACK (if revising):
{feedback}
"""


def _extract_niche(messages: list[Any]) -> str:
    """Pull the user brief from the message history."""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            return msg.get("content", "")
        if isinstance(msg, str):
            return msg
    return ""


@validate_node_output
async def creative_worker_node(state: dict[str, Any]) -> dict[str, Any]:
    """Creative Worker — generates content via LLM."""
    persona = state.get("persona")
    feedback = state.get("feedback")
    retry_count = state.get("retry_count", 0)
    messages = state.get("messages", [])
    campaign_id = state.get("campaign_id", "unknown")

    niche = _extract_niche(messages)
    is_revision = feedback is not None and retry_count > 0

    logs_out: list[str] = []
    stage = "revising" if is_revision else "draft"

    if is_revision:
        logs_out.append(
            f"[Creative] Attempt #{retry_count + 1} — incorporating feedback: "
            f"\"{feedback[:80]}...\""
        )
    else:
        logs_out.append("[Creative] Generating initial draft...")

    # ── Prepare LLM ──
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
    ).with_structured_output(MarketingContent)

    prompt = ChatPromptTemplate.from_messages([
        ("system", _CREATIVE_SYSTEM_PROMPT),
        ("user", _CREATIVE_USER_PROMPT),
    ])
    chain = prompt | llm

    # Fallbacks in case state is malformed
    tone = persona.tone if persona else "Professional"
    visuals = f"{persona.visual_style} ({persona.visual_mood})" if persona else "Clean"
    philosophy = persona.brand_philosophy if persona else "Neutral"
    forbidden = (
        ", ".join(persona.prohibited_terms)
        if persona and persona.prohibited_terms
        else "None"
    )

    input_vars = {
        "tone": tone,
        "visuals": visuals,
        "philosophy": philosophy,
        "forbidden_terms": forbidden,
        "niche": niche,
        "feedback": feedback if is_revision else "None (First pass)",
    }

    if os.getenv("AGENCY_MOCK_LLM", "false").lower() == "true":
        logs_out.append("[Creative] MOCK MODE ACTIVE: Bypassing Gemini API.")
        await asyncio.sleep(2)
        content = MarketingContent(
            caption="[MOCK CAPTION] This is a hardcoded placeholder caption generated in Mock Mode to prevent token burn.",
            image_prompt="[MOCK PROMPT] A generic, aesthetic placeholder image prompt.",
            publish_targets=["instagram"]
        )
    else:
        logs_out.append("[Creative] Invoking LLM (thinking...)")
    
        try:
            # Wrapped in tenacity retry policy
            content: MarketingContent = await resilient_call(
                chain.ainvoke,
                input_vars,
                operation_name="creative_worker_llm",
            )
        except Exception as e:
            logger.error("Creative LLM failed: %s", e)
            logs_out.append(f"[Creative] ✗ LLM failure: {str(e)}")
            raise

    logs_out.append(
        f"[Creative] Draft ready — caption: {len(content.caption)} chars, "
        f"image_prompt: {len(content.image_prompt)} chars"
    )

    logger.info(
        "Creative worker complete  campaign=%s  stage=%s  revision=%s",
        campaign_id, stage, is_revision,
    )

    return {
        "content": content,
        "drafts": [content],  # Appends to state.drafts
        "stage": stage,
        "logs": logs_out,
    }
