"""
CONTRACTS.py — The Single Source of Truth for Agency V3.

This file defines every Pydantic model, typed enum, state contract,
and API envelope used across the multi-agent swarm.  It is the SOLE
authority referenced by:

    - LangGraph nodes (creative, critic, executive, image, publisher)
    - The FastAPI transport layer (webhook, REST endpoints, SSE)
    - The React frontend SDK (compiled to types.ts via OpenAPI)
    - BRIDGE_SPEC.md (interface control document)
    - AGENCY_PROTOCOLS.md (behavioral constitution)

Rules:
    1. ZERO agent logic, ZERO database imports, ZERO orchestration.
    2. Every new field MUST have a default value (schema migration safety).
    3. Breaking changes require a version bump and dual-field coexistence.
    4. This file is imported as `from CONTRACTS import ...` — keep it flat.

Version: 3.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import TypedDict


# ═══════════════════════════════════════════════════════════════════════════
# §1  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# --- Brand & Aesthetic ---

BrandTone = Literal[
    "Stoic",
    "Analytical",
    "Post-Punk",
    "Melancholic",
    "Sardonic",
    "Custom",
]
"""
The tonal register of the persona's written output.
'Custom' requires a non-empty `custom_tone_description` on PersonaConfig.
"""

VisualMood = Literal[
    "High-Contrast B&W",
    "Desaturated Color",
    "Neon Noir",
    "Archival Film",
    "Custom",
]
"""
The dominant visual language for image generation prompts.
Each mood maps to a prefix template in the image worker.
"""


# --- Campaign Lifecycle ---

CampaignStage = Literal[
    "draft",            # Creative is generating initial content
    "reviewing",        # Critic is evaluating the content
    "revising",         # Creative is incorporating critic feedback
    "generating_image", # Image worker is producing visuals
    "awaiting_approval",# HITL gate — waiting for director decision
    "approved",         # Director approved — queued for publish
    "published",        # Content delivered to target platform
    "vetoed",           # Director rejected the content
    "failed",           # Unrecoverable error in the pipeline
]

CriticGrade = Literal["PASS", "REVISION"]

BriefingRecommendation = Literal["SHIP", "REVIEW", "HOLD"]


# --- Platform & Channel ---

PublishTarget = Literal[
    "instagram",
    "threads",
]
"""
The social platform where approved content is delivered.
Each target has its own API adapter and format constraints.
"""

InteractionChannel = Literal[
    "whatsapp",
    "web_ui",
]
"""
The channel through which the Director interacts with the agency.
WhatsApp supports limited HITL actions (approve/reject only).
Web UI supports full HITL actions (approve, reject, edit, revise).
"""


# ═══════════════════════════════════════════════════════════════════════════
# §2  PERSONA SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

class PersonaConfig(BaseModel):
    """The brand identity configuration injected into every agent.

    A persona defines the creative DNA of the agency for a given client
    or campaign.  It controls tone, visual language, philosophical
    grounding, and the vocabulary register that all agents must obey.

    The persona is immutable once a campaign is initiated — mid-campaign
    persona changes are a source of Campaign Drift and are prohibited.
    """

    name: str = Field(
        description="Human-readable persona identifier (e.g. 'Silicon Labor')"
    )
    tone: BrandTone = Field(
        description="The tonal register for written output"
    )
    custom_tone_description: Optional[str] = Field(
        default=None,
        description=(
            "Required when tone='Custom'. A 1-2 sentence description "
            "of the desired tonal register."
        ),
    )
    visual_style: str = Field(
        description=(
            "Freeform visual direction for image generation. "
            "E.g. 'High-contrast B&W, harsh shadows, 35mm grain'"
        )
    )
    visual_mood: VisualMood = Field(
        default="High-Contrast B&W",
        description="The dominant visual mood — maps to image prompt prefixes",
    )
    brand_philosophy: str = Field(
        description=(
            "The intellectual/philosophical framework that grounds the brand. "
            "E.g. 'Byung-Chul Han's Burnout Society / Baudrillard's hyper-reality'"
        )
    )
    vocabulary_register: list[str] = Field(
        default_factory=list,
        description=(
            "Key terms and phrases the persona should naturally employ. "
            "E.g. ['transparency', 'burnout', 'hyper-reality', 'simulation']"
        ),
    )
    prohibited_terms: list[str] = Field(
        default_factory=list,
        description=(
            "Words and phrases that are absolutely banned from this persona's output. "
            "E.g. ['game-changer', 'revolutionary', 'unleash', 'skyrocket']"
        ),
    )
    default_aspect_ratio: str = Field(
        default="9:16",
        description="Default aspect ratio for generated images",
    )
    default_publish_targets: list[PublishTarget] = Field(
        default_factory=lambda: ["instagram"],
        description="Default platforms for content delivery",
    )

    @model_validator(mode="after")
    def _validate_custom_tone(self) -> "PersonaConfig":
        if self.tone == "Custom" and not self.custom_tone_description:
            raise ValueError(
                "custom_tone_description is required when tone='Custom'"
            )
        return self


# ---------------------------------------------------------------------------
# Built-in Personas (Test & Production)
# ---------------------------------------------------------------------------

PERSONA_NOCTURNAL_AUDITOR = PersonaConfig(
    name="Silicon Labor",
    tone="Stoic",
    visual_style="High-contrast B&W, harsh shadows, 35mm grain",
    visual_mood="High-Contrast B&W",
    brand_philosophy="Byung-Chul Han's Burnout Society / Baudrillard's hyper-reality",
    vocabulary_register=[
        "transparency", "burnout", "fatigue", "simulation",
        "the copy", "the hyperreal", "smooth surfaces",
        "digital silence", "exhaustion", "achievement-subject",
    ],
    prohibited_terms=[
        "game-changer", "revolutionary", "unleash", "skyrocket",
        "amazing", "incredible", "best ever", "don't miss out",
        "limited time", "act now", "exclusive offer",
    ],
    default_aspect_ratio="9:16",
    default_publish_targets=["instagram", "threads"],
)

PERSONA_VELVET_DISPATCH = PersonaConfig(
    name="Velvet Dispatch",
    tone="Melancholic",
    visual_style="Desaturated teal and amber, soft grain, golden hour haze",
    visual_mood="Desaturated Color",
    brand_philosophy=(
        "Walter Benjamin's 'The Work of Art in the Age of Mechanical Reproduction' — "
        "aura, nostalgia, and the melancholy of objects stripped of their origin"
    ),
    vocabulary_register=[
        "aura", "reproduction", "nostalgia", "patina",
        "provenance", "the original", "mechanical",
        "distance", "trace", "fading",
    ],
    prohibited_terms=[
        "game-changer", "revolutionary", "unleash", "amazing",
        "incredible", "hurry", "flash sale", "FOMO",
        "best ever", "once in a lifetime",
    ],
    default_aspect_ratio="4:5",
    default_publish_targets=["instagram"],
)

PERSONA_FERRO_STATIC = PersonaConfig(
    name="Ferro Static",
    tone="Sardonic",
    visual_style="Neon-lit industrial, cyberpunk grain, deep blacks with electric accents",
    visual_mood="Neon Noir",
    brand_philosophy=(
        "Mark Fisher's Capitalist Realism — the impossibility of imagining "
        "alternatives, hauntology, and the slow cancellation of the future"
    ),
    vocabulary_register=[
        "capitalist realism", "hauntology", "the weird",
        "lost futures", "nostalgia mode", "depressive hedonia",
        "the eerie", "cancelled future", "reflexive impotence",
    ],
    prohibited_terms=[
        "game-changer", "disruptive", "synergy", "leverage",
        "unlock your potential", "empower", "thrive",
        "crushing it", "hustle", "grind",
    ],
    default_aspect_ratio="9:16",
    default_publish_targets=["threads"],
)

# Registry — workers can look up personas by name
PERSONA_REGISTRY: dict[str, PersonaConfig] = {
    "Silicon Labor": PERSONA_NOCTURNAL_AUDITOR,
    "Velvet Dispatch": PERSONA_VELVET_DISPATCH,
    "Ferro Static": PERSONA_FERRO_STATIC,
}


# ═══════════════════════════════════════════════════════════════════════════
# §3  DOMAIN MODELS
# ═══════════════════════════════════════════════════════════════════════════

class MarketingContent(BaseModel):
    """The primary output artifact produced by the Creative Worker.

    This model represents a single piece of marketing content — a caption
    and an image generation directive — that flows through the entire
    evaluator-optimizer loop.

    The field validators act as the FIRST guardrail layer, catching
    structural violations before the Critic ever sees the content.
    """

    caption: str = Field(
        description=(
            "The social media copy.  Must align with the persona's tone "
            "and vocabulary register.  Emoji usage is validated by the "
            "Critic, not at the schema level (LLM output may need correction)."
        )
    )
    image_prompt: str = Field(
        description=(
            "The technical prompt for the image generation service.  "
            "Must align with the persona's visual_style and visual_mood."
        )
    )
    aspect_ratio: str = Field(
        default="9:16",
        description="Target aspect ratio for the generated image",
    )
    vibe_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Float 0-10 expressing persona alignment (set by Critic)",
    )
    needs_revision: bool = Field(
        default=False,
        description="Flag set by the Critic when content fails audit",
    )
    image_urls: list[str] = Field(
        default_factory=list,
        description="Public URLs or local paths of generated images (set by Image Worker)",
    )
    publish_targets: list[PublishTarget] = Field(
        default_factory=lambda: ["instagram"],
        description="Platforms this content is destined for",
    )

    @field_validator("aspect_ratio")
    @classmethod
    def _validate_aspect_ratio(cls, v: str) -> str:
        allowed = {"9:16", "4:5", "1:1", "16:9"}
        if v not in allowed:
            raise ValueError(
                f"aspect_ratio must be one of {allowed}, got '{v}'"
            )
        return v


class Critique(BaseModel):
    """Evaluation artifact returned by the Critic Worker.

    The Critic grades content against the persona's constraints and
    produces actionable feedback.  The grade directly controls the
    conditional edge in the LangGraph evaluator-optimizer loop.
    """

    grade: CriticGrade = Field(
        description="PASS if the content meets all constraints, REVISION otherwise",
    )
    feedback: str = Field(
        description=(
            "Detailed, constructive feedback for the Creative Worker. "
            "Must reference specific failures (emoji usage, hype-language, "
            "visual constraint violations) when grade is REVISION."
        )
    )
    vibe_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Float 0-10 rating of persona alignment",
    )


class ExecutiveBriefing(BaseModel):
    """Structured output from the Executive Worker.

    Translates raw production data — critic feedback, vibe scores,
    revision counts — into a concise, professional director-level summary.
    """

    summary: str = Field(
        description=(
            "A 3-5 sentence executive summary of the current campaign draft. "
            "Professional tone, no jargon.  Highlight the creative direction "
            "and any quality concerns."
        )
    )
    risk_flags: list[str] = Field(
        default_factory=list,
        description=(
            "Specific risk items: brand misalignment, visual constraint "
            "violations, excessive revision loops, etc."
        ),
    )
    recommendation: BriefingRecommendation = Field(
        description="One of: SHIP, REVIEW, or HOLD",
    )


class JudgeScores(BaseModel):
    """1-5 rubric scores from the evaluation Judge (4 dimensions).

    Used by the lab evaluation harness to compare Student output
    against Teacher gold standards.
    """

    philosophy_fidelity: int = Field(
        ge=1, le=5,
        description="1=Marketing hype; 5=Deep philosophical observation",
    )
    visual_aesthetic: int = Field(
        ge=1, le=5,
        description="1=Generic prompt; 5=Precise, atmospheric prompt with style constraints",
    )
    tone_consistency: int = Field(
        ge=1, le=5,
        description="1=Emojis/hype; 5=Detached, objective-led observation",
    )
    visual_execution: int = Field(
        ge=1, le=5,
        description=(
            "1=Wrong style/aspect ratio or severe artifacts; "
            "5=Publication-ready, matches persona visual style"
        ),
    )
    rationale: str = Field(
        description="Specific citations justifying each score",
    )


class RevisionEntry(BaseModel):
    """A single creative → critic exchange in the revision history.

    Stored as an audit trail in the graph state to prevent amnesia
    across revision loops and support post-mortem analysis.
    """

    attempt: int = Field(ge=1, description="1-indexed attempt number")
    caption_snapshot: str = Field(description="Caption at this revision")
    image_prompt_snapshot: str = Field(description="Image prompt at this revision")
    critic_grade: CriticGrade
    critic_feedback: str
    vibe_score: float = Field(ge=0.0, le=10.0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


# ═══════════════════════════════════════════════════════════════════════════
# §4  GRAPH STATE
# ═══════════════════════════════════════════════════════════════════════════

class V3AgencyState(TypedDict):
    """Shared state flowing through the LangGraph evaluator-optimizer loop.

    This is the V3 evolution of AgencyState.  All V2 fields are preserved
    with identical semantics.  New fields have defaults so that threads
    serialized under the V2 schema can still be deserialized.

    Lifecycle:
        START → creative_worker → critic_worker → [revise loop]
              → image_worker → wait_for_approval → [HITL interrupt]
              → publisher → END

    Conditional routing:
        content.needs_revision == True  → route back to creative_worker
        content.needs_revision == False → route to image_worker

    Guardrail fields:
        retry_count — incremented by Critic on REVISION; the Loop
        Sentinel forces approval at >= MAX_REVISIONS.
    """

    # ── Core pipeline state (V2-compatible) ──
    messages: list[Any]
    persona: PersonaConfig
    content: Optional[MarketingContent]
    feedback: Optional[str]          # Critic writes, Creative reads
    retry_count: int                 # loop sentinel — prevents infinite revisions

    # ── Cockpit fields (V2-compatible) ──
    executive_briefing: Optional[str]
    approval_mode: Optional[str]     # "active" | "passive"
    shadow_mode: bool                # if True, publisher becomes debug-only

    # ── Error recovery (V2-compatible) ──
    last_error: Optional[str]

    # ── V3 additions ──
    campaign_id: Optional[str]       # links to CockpitCampaign DB record
    stage: Optional[CampaignStage]   # explicit lifecycle position
    revision_history: list[RevisionEntry]  # full audit trail
    publish_targets: list[PublishTarget]   # where to deliver approved content
    interaction_channel: Optional[InteractionChannel]  # where HITL commands arrive


# ═══════════════════════════════════════════════════════════════════════════
# §5  API CONTRACTS (BRIDGE)
# ═══════════════════════════════════════════════════════════════════════════

# --- Standard Response Envelope ---

class APIMeta(BaseModel):
    """Metadata block for every API response."""
    thread_id: str = Field(description="LangGraph thread identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    version: str = Field(default="v3.0.0")


class APIEnvelope(BaseModel):
    """Standard wrapper for all REST API responses.

    Defined in BRIDGE_SPEC.md §1: The Handshake.
    """
    status: Literal["success", "error"] = "success"
    data: Any = Field(default=None, description="Response payload")
    meta: APIMeta


# --- Request Bodies ---

class CampaignStartRequest(BaseModel):
    """POST /campaign/start — Initialize a new campaign thread.

    The client can specify a persona by name (looked up from the registry)
    or provide a full PersonaConfig for custom personas.
    """
    persona_name: Optional[str] = Field(
        default=None,
        description="Name of a registered persona (e.g. 'Silicon Labor')",
    )
    persona_config: Optional[PersonaConfig] = Field(
        default=None,
        description="Full custom persona config (overrides persona_name)",
    )
    niche: str = Field(
        description="The business/product brief for the campaign",
    )
    publish_targets: list[PublishTarget] = Field(
        default_factory=lambda: ["instagram"],
        description="Target platforms for the generated content",
    )

    @model_validator(mode="after")
    def _validate_persona_source(self) -> "CampaignStartRequest":
        if not self.persona_name and not self.persona_config:
            raise ValueError(
                "Either persona_name or persona_config must be provided"
            )
        return self


class CampaignResumeRequest(BaseModel):
    """POST /campaign/{id}/resume — Submit HITL approval or feedback.

    WhatsApp channel supports: approve, reject.
    Web UI channel supports:   approve, reject, edit, request_revision.
    """
    decision: Literal["approve", "reject", "edit", "request_revision"] = Field(
        description="The director's decision on the pending content",
    )
    feedback: Optional[str] = Field(
        default=None,
        description=(
            "Director's notes.  Required for 'reject' and 'request_revision'. "
            "Optional for 'approve'.  Ignored for 'edit' (use edited_content)."
        ),
    )
    edited_content: Optional[MarketingContent] = Field(
        default=None,
        description="Full replacement content — only used with decision='edit'",
    )
    channel: InteractionChannel = Field(
        default="web_ui",
        description="Source channel of this HITL action",
    )

    @model_validator(mode="after")
    def _validate_decision_payload(self) -> "CampaignResumeRequest":
        if self.decision == "edit" and not self.edited_content:
            raise ValueError(
                "edited_content is required when decision='edit'"
            )
        if self.decision in ("reject", "request_revision") and not self.feedback:
            raise ValueError(
                f"feedback is required when decision='{self.decision}'"
            )
        # WhatsApp channel restrictions
        if self.channel == "whatsapp" and self.decision not in ("approve", "reject"):
            raise ValueError(
                f"WhatsApp channel only supports 'approve' and 'reject', "
                f"got '{self.decision}'"
            )
        return self


# --- SSE Event Models ---

class SSEEventNodeStart(BaseModel):
    """SSE event: a specific agent has begun work."""
    event_type: Literal["node_start"] = "node_start"
    node_name: str


class SSEEventAgentThought(BaseModel):
    """SSE event: real-time streaming of agent reasoning."""
    event_type: Literal["agent_thought"] = "agent_thought"
    text: str
    step: int = 0


class SSEEventBreakpoint(BaseModel):
    """SSE event: graph paused for Director intervention."""
    event_type: Literal["breakpoint"] = "breakpoint"
    breakpoint_type: Literal["approval_required"] = "approval_required"
    approval_mode: Literal["active", "passive"]
    preview: Optional[MarketingContent] = None


class SSEEventCompletion(BaseModel):
    """SSE event: campaign is finalized."""
    event_type: Literal["completion"] = "completion"
    stage: CampaignStage
    publish_targets: list[PublishTarget] = Field(default_factory=list)


class SSEEventError(BaseModel):
    """SSE event: an error occurred during processing."""
    event_type: Literal["error"] = "error"
    error_code: int
    message: str
    node_name: Optional[str] = None


# Union for type-safe SSE dispatch
SSEEvent = Union[
    SSEEventNodeStart,
    SSEEventAgentThought,
    SSEEventBreakpoint,
    SSEEventCompletion,
    SSEEventError,
]


# ═══════════════════════════════════════════════════════════════════════════
# §6  GUARDRAIL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

class GuardrailConfig(BaseModel):
    """Centralized guardrail thresholds for the Agency V3 pipeline.

    These are the "physics constants" of the swarm.  Changing them
    affects cost, quality, and latency.  All values are documented
    with their downstream impact.
    """

    # --- Evaluator-Optimizer Loop ---
    max_revisions: int = Field(
        default=3,
        ge=1, le=10,
        description=(
            "Hard ceiling on creative→critic revision loops. "
            "Prevents recursive token sink.  At this limit, "
            "the Critic force-passes the content."
        ),
    )
    recursion_limit: int = Field(
        default=15,
        ge=5, le=100,
        description=(
            "LangGraph graph.compile(recursion_limit=N). "
            "Hard stop for the entire graph execution."
        ),
    )

    # --- FinOps: Per-Node Token Budgets ---
    creative_request_limit: int = Field(
        default=5,
        description="Max LLM requests per creative_worker invocation",
    )
    creative_token_limit: int = Field(
        default=5000,
        description="Max input tokens per creative_worker invocation",
    )
    critic_request_limit: int = Field(
        default=5,
        description="Max LLM requests per critic_worker invocation",
    )
    critic_token_limit: int = Field(
        default=5000,
        description="Max input tokens per critic_worker invocation",
    )

    # --- HITL Thresholds ---
    passive_approval_threshold: float = Field(
        default=8.5,
        ge=0.0, le=10.0,
        description=(
            "vibe_score >= this value triggers Passive approval path "
            "(auto-approve countdown).  Below this → Active (manual)."
        ),
    )

    # --- Retry & Resilience ---
    transient_retry_attempts: int = Field(
        default=3,
        ge=1, le=10,
        description="Tenacity retry attempts for transient API errors",
    )
    transient_retry_min_wait: float = Field(
        default=2.0,
        description="Minimum backoff wait in seconds",
    )
    transient_retry_max_wait: float = Field(
        default=15.0,
        description="Maximum backoff wait in seconds",
    )


# Default guardrails — importable by all workers
DEFAULT_GUARDRAILS = GuardrailConfig()
