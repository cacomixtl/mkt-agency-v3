/**
 * contracts.ts — Strict TypeScript representation of CONTRACTS.py
 *
 * This file is the frontend's single source of truth for all typed
 * enums, models, request/response shapes, and SSE event payloads.
 * Every interface and type literal here maps 1:1 to a Pydantic model
 * or Python Literal in CONTRACTS.py v3.0.0.
 *
 * Rules:
 *   1. No UI logic, no React imports, no component code.
 *   2. Every field mirrors the Python default (undefined = no default in Python).
 *   3. Breaking changes here require a version bump in CONTRACTS.py first.
 */

// ═══════════════════════════════════════════════════════════════════════════
// §1  ENUMS & CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

/** The tonal register of the persona's written output. */
export type BrandTone =
  | 'Stoic'
  | 'Analytical'
  | 'Post-Punk'
  | 'Melancholic'
  | 'Sardonic'
  | 'Custom';

/** The dominant visual language for image generation prompts. */
export type VisualMood =
  | 'High-Contrast B&W'
  | 'Desaturated Color'
  | 'Neon Noir'
  | 'Archival Film'
  | 'Custom';

/** Campaign lifecycle position — the spine of the Director's Cockpit. */
export type CampaignStage =
  | 'draft'
  | 'reviewing'
  | 'revising'
  | 'generating_image'
  | 'awaiting_approval'
  | 'approved'
  | 'published'
  | 'vetoed'
  | 'failed';

export type CriticGrade = 'PASS' | 'REVISION';

export type BriefingRecommendation = 'SHIP' | 'REVIEW' | 'HOLD';

/** The social platform where approved content is delivered. */
export type PublishTarget = 'instagram' | 'threads';

/** The channel through which the Director interacts with the agency. */
export type InteractionChannel = 'whatsapp' | 'web_ui';

/** Aspect ratios validated by the Pydantic schema. */
export type AspectRatio = '9:16' | '4:5' | '1:1' | '16:9';

// ═══════════════════════════════════════════════════════════════════════════
// §2  PERSONA SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

export interface PersonaConfig {
  name: string;
  tone: BrandTone;
  custom_tone_description?: string | null;
  visual_style: string;
  visual_mood: VisualMood;
  brand_philosophy: string;
  vocabulary_register: string[];
  prohibited_terms: string[];
  default_aspect_ratio: AspectRatio;
  default_publish_targets: PublishTarget[];
}

// ═══════════════════════════════════════════════════════════════════════════
// §3  DOMAIN MODELS
// ═══════════════════════════════════════════════════════════════════════════

export interface MarketingContent {
  caption: string;
  image_prompt: string;
  aspect_ratio: AspectRatio;
  vibe_score?: number | null;
  needs_revision: boolean;
  image_urls: string[];
  publish_targets: PublishTarget[];
}

export interface Critique {
  grade: CriticGrade;
  feedback: string;
  vibe_score: number;
}

export interface ExecutiveBriefing {
  summary: string;
  risk_flags: string[];
  recommendation: BriefingRecommendation;
}

export interface JudgeScores {
  philosophy_fidelity: number;
  visual_aesthetic: number;
  tone_consistency: number;
  visual_execution: number;
  rationale: string;
}

export interface RevisionEntry {
  attempt: number;
  caption_snapshot: string;
  image_prompt_snapshot: string;
  critic_grade: CriticGrade;
  critic_feedback: string;
  vibe_score: number;
  timestamp: string; // ISO-8601
}

// ═══════════════════════════════════════════════════════════════════════════
// §4  GRAPH STATE
// ═══════════════════════════════════════════════════════════════════════════

export interface V3AgencyState {
  // Core pipeline state (V2-compatible)
  messages: unknown[];
  persona: PersonaConfig;
  content: MarketingContent | null;
  feedback: string | null;
  retry_count: number;

  // Cockpit fields (V2-compatible)
  executive_briefing: string | null;
  approval_mode: 'active' | 'passive' | null;
  shadow_mode: boolean;

  // Error recovery (V2-compatible)
  last_error: string | null;

  // V3 additions
  campaign_id: string | null;
  stage: CampaignStage | null;
  revision_history: RevisionEntry[];
  publish_targets: PublishTarget[];
  interaction_channel: InteractionChannel | null;
}

// ═══════════════════════════════════════════════════════════════════════════
// §5  API CONTRACTS (BRIDGE)
// ═══════════════════════════════════════════════════════════════════════════

export interface APIMeta {
  thread_id: string;
  timestamp: string; // ISO-8601
  version: string;
}

export interface APIEnvelope<T = unknown> {
  status: 'success' | 'error';
  data: T;
  meta: APIMeta;
}

// --- Request Bodies ---

export interface CampaignStartRequest {
  persona_name?: string | null;
  persona_config?: PersonaConfig | null;
  niche: string;
  publish_targets: PublishTarget[];
}

export type HITLDecision = 'approve' | 'reject' | 'edit' | 'request_revision';

export interface CampaignResumeRequest {
  decision: HITLDecision;
  feedback?: string | null;
  edited_content?: MarketingContent | null;
  channel: InteractionChannel;
}

// --- SSE Event Models ---

export interface SSEEventNodeStart {
  event_type: 'node_start';
  node_name: string;
}

export interface SSEEventAgentThought {
  event_type: 'agent_thought';
  text: string;
  step: number;
}

export interface SSEEventBreakpoint {
  event_type: 'breakpoint';
  breakpoint_type: 'approval_required';
  approval_mode: 'active' | 'passive';
  preview: MarketingContent | null;
}

export interface SSEEventCompletion {
  event_type: 'completion';
  stage: CampaignStage;
  publish_targets: PublishTarget[];
}

export interface SSEEventError {
  event_type: 'error';
  error_code: number;
  message: string;
  node_name?: string | null;
}

/** Discriminated union of all SSE event types. */
export type SSEEvent =
  | SSEEventNodeStart
  | SSEEventAgentThought
  | SSEEventBreakpoint
  | SSEEventCompletion
  | SSEEventError;
