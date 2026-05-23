"""
logic.nodes.judge — Judge (Critic) Worker Node.

Evaluates marketing content against the PersonaConfig using an LLM.
Produces a ``Critique`` artifact which controls the routing loop.
Wrapped with resilience layers and output validation.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from CONTRACTS import DEFAULT_GUARDRAILS, Critique, RevisionEntry
from guardrails import resilient_call, validate_node_output

logger = logging.getLogger(__name__)

_JUDGE_SYSTEM_PROMPT = """You are the elite Brand Compliance Judge.
Evaluate the Draft Marketing Content against the Brand Context constraints.

BRAND CONTEXT:
Tone & Voice: {tone}
Visual Aesthetic: {visuals}
Brand Philosophy: {philosophy}
Forbidden Terms: {forbidden_terms}

EVALUATION RULES:
1. Return a structured Critique object.
2. `grade` MUST be "PASS" if the content strictly follows all constraints and contains NO emojis.
3. `grade` MUST be "REVISION" if emojis are used, forbidden terms are present, or tone/visuals/philosophy misalign.
4. If "REVISION", `feedback` must explicitly cite the exact failure.
5. Provide a `vibe_score` (0.0 to 10.0) representing brand alignment.
"""

_JUDGE_USER_PROMPT = """DRAFT CONTENT:
Caption: {caption}
Image Prompt: {image_prompt}
"""


@validate_node_output
async def judge_worker_node(state: dict[str, Any]) -> dict[str, Any]:
    """Judge Worker — evaluates content via LLM."""
    persona = state.get("persona")
    content = state.get("content")
    retry_count = state.get("retry_count", 0)
    campaign_id = state.get("campaign_id", "unknown")
    max_revisions = DEFAULT_GUARDRAILS.max_revisions

    logs_out: list[str] = []
    logs_out.append(
        f"[Judge] Auditing draft (attempt #{retry_count + 1}/{max_revisions})"
    )

    if not content:
        raise ValueError("Judge node called but no content exists in state.")

    caption = content.caption
    image_prompt = content.image_prompt

    # ── Prepare LLM ──
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,  # Low temp for analytical consistency
    ).with_structured_output(Critique)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _JUDGE_SYSTEM_PROMPT),
            ("user", _JUDGE_USER_PROMPT),
        ]
    )
    chain = prompt | llm

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
        "caption": caption,
        "image_prompt": image_prompt,
    }

    if os.getenv("AGENCY_MOCK_LLM", "false").lower() == "true":
        logs_out.append("[Judge] MOCK MODE ACTIVE: Auto-passing content.")
        await asyncio.sleep(1.5)
        critique = Critique(grade="PASS", feedback="Mock approval.", vibe_score=9.5)
    else:
        logs_out.append("[Judge] Invoking LLM auditor (thinking...)")

        try:
            critique: Critique = await resilient_call(
                chain.ainvoke,
                input_vars,
                operation_name="judge_worker_llm",
            )
        except Exception as e:
            logger.error("Judge LLM failed: %s", e)
            logs_out.append(f"[Judge] ✗ LLM failure: {str(e)}")
            raise

    grade = critique.grade
    vibe_score = critique.vibe_score
    feedback = critique.feedback

    # ── FinOps Guardrail: Force PASS at ceiling ──
    force_passed = False
    if grade == "REVISION" and retry_count >= max_revisions:
        grade = "PASS"
        force_passed = True
        feedback = (
            f"FINOPS OVERRIDE: Max revisions reached. Original critique: {feedback}"
        )
        logs_out.append(
            f"[Judge] ⚠ FinOps override — force PASS at retry_count={retry_count}"
        )

    logs_out.append(
        f"[Judge] Verdict: {grade} — vibe_score={vibe_score:.1f}"
        f"{' (FORCE-PASSED)' if force_passed else ''}"
    )
    if grade == "REVISION":
        logs_out.append(f"[Judge] Feedback: {feedback}")

    # ── Mutate Content & State ──
    updated_content = content.model_copy(
        update={
            "vibe_score": vibe_score,
            "needs_revision": grade == "REVISION",
        }
    )

    revision_entry = RevisionEntry(
        attempt=retry_count + 1,
        caption_snapshot=caption,
        image_prompt_snapshot=image_prompt,
        critic_grade=grade,
        critic_feedback=feedback,
        vibe_score=vibe_score,
    )

    new_retry_count = retry_count + 1 if grade == "REVISION" else retry_count

    logger.info(
        "Judge worker complete  campaign=%s  grade=%s  vibe=%.1f",
        campaign_id,
        grade,
        vibe_score,
    )

    return {
        "content": updated_content,
        "feedback": feedback if grade == "REVISION" else None,
        "retry_count": new_retry_count,
        "stage": "reviewing",
        "revision_history": [revision_entry],  # Appends via operator.add
        "logs": logs_out,
    }
