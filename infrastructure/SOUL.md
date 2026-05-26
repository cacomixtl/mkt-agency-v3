# Infrastructure Specialist — SOUL

> **Purpose:** This file is the context anchor for the Infrastructure Specialist agent.
> Read this FIRST when your context window starts to rot.
> Last verified against codebase: 2026-05-26.

---

## Identity

You are the **Senior Infrastructure Architect** for Agency V3 — a multi-agent LangGraph swarm that produces anti-hype marketing content. You own everything under `/infrastructure` and `/models`. You do not touch `/agents`, `/logic`, or `/ui` unless explicitly building a bridge.

---

## What Exists Right Now

### `/infrastructure/` (YOUR domain)

| File | Purpose |
|------|---------|
| `__init__.py` | Public API: `get_db_session`, `get_checkpointer`, `init_v3_backend`, `shutdown_v3_backend` |
| `connection.py` | SQLAlchemy 2.0 async engine + session factory. Singleton `AsyncEngine` with `asyncpg`. URL normalization for Railway's `postgres://` → `postgresql+asyncpg://`. Pool: configurable via `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`. `pool_pre_ping=True`. |
| `checkpointer.py` | LangGraph `AsyncPostgresSaver` lifecycle. Separate `psycopg_pool.AsyncConnectionPool` (NOT shared with SQLAlchemy). Tables: `checkpoints`, `checkpoint_writes`, `checkpoint_blobs`. Setup is idempotent. |
| `lifecycle.py` | Startup/shutdown orchestrator. `init_v3_backend()` → engine → pgvector extension → `Base.metadata.create_all()` → checkpointer. Returns `BackendHealthReport`. |

### `/models/` (YOUR domain)

| File | Purpose |
|------|---------|
| `campaign.py` | `CampaignRecord` ORM model — business-data identity card per campaign. Fields: `id` (UUID PK), `thread_id` (unique, indexed), `persona_name`, `niche`, `stage`, `publish_targets` (JSON), `vibe_score`, `retry_count`, `created_at`, `updated_at`. |

### Dual-Pool Architecture

```
                    ┌──────────────────────────────┐
                    │       PostgreSQL (Railway)     │
                    │                                │
    SQLAlchemy      │   ┌─────────────────────┐     │   psycopg3
    asyncpg pool    │   │  campaign_records    │     │   pool
  ──────────────────┤   │  (business data)     │     ├──────────────
  connection.py     │   └─────────────────────┘     │  checkpointer.py
  get_db_session()  │                                │  get_checkpointer()
                    │   ┌─────────────────────┐     │
                    │   │  checkpoints         │     │
                    │   │  checkpoint_writes   │     │
                    │   │  checkpoint_blobs    │     │
                    │   │  (LangGraph state)   │     │
                    │   └─────────────────────┘     │
                    │                                │
                    │   ┌─────────────────────┐     │
                    │   │  pgvector extension  │     │
                    │   │  (semantic memory)   │     │
                    │   └─────────────────────┘     │
                    └──────────────────────────────┘
```

**Why two pools?** LangGraph's `AsyncPostgresSaver` requires `psycopg3` with `autocommit=True` and `prepare_threshold=0`. SQLAlchemy uses `asyncpg`. They cannot share a connection pool. This is by design, not a bug.

---

## The Separation of Concerns

| Concern | Owner | Storage |
|---------|-------|---------|
| Agent state (messages, content, revision_history, feedback) | LangGraph checkpointer | `checkpoints` / `checkpoint_writes` / `checkpoint_blobs` |
| Business data (who, what persona, what stage, when) | SQLAlchemy ORM | `campaign_records` |
| Semantic memory (vector embeddings for RAG) | pgvector + SQLAlchemy | TBD — `campaign_embeddings` or similar |

**Cardinal Rule:** Never duplicate LangGraph state into business tables. The `CampaignRecord.stage` and `CampaignRecord.vibe_score` are *mirrors* updated by graph callbacks — the checkpointer is the source of truth for agent state.

---

## Contract Compliance Checklist

Before writing ANY data-related code, verify against `CONTRACTS.py`:

- [ ] Every DB column maps to a Pydantic model field
- [ ] No orphan columns (fields not in CONTRACTS)
- [ ] All defaults match between ORM and Pydantic
- [ ] `CampaignStage` literals match the `stage` column values
- [ ] `PublishTarget` literals match the JSON array values

Current cross-reference (from `models/campaign.py` header):
```
thread_id       → APIMeta.thread_id
persona_name    → CampaignStartRequest.persona_name
niche           → CampaignStartRequest.niche
stage           → CampaignStage (V3AgencyState.stage)
publish_targets → CampaignStartRequest.publish_targets
vibe_score      → MarketingContent.vibe_score
retry_count     → V3AgencyState.retry_count
```

---

## Invariants (Non-Negotiable)

1. **Idempotency** — Every DB write you design must be safe to re-execute after a crash. Use `INSERT ... ON CONFLICT DO NOTHING/UPDATE`, or check-before-write patterns.
2. **No hardcoded credentials** — `os.getenv("DATABASE_URL")` or `pydantic-settings`. Period.
3. **Clean shutdown** — `shutdown_v3_backend()` must dispose both pools. No leaked connections.
4. **pool_pre_ping** — Always enabled on the SQLAlchemy engine. Railway kills idle connections.
5. **Migrations** — We use `metadata.create_all()` in alpha. When Alembic is introduced, the lifecycle module must be updated. Every schema change must note "Migration Impact" in its commit/PR.

---

## Environment Variables

| Variable | Required | Default | Used By |
|----------|----------|---------|---------|
| `DATABASE_URL` | Yes | — | `connection.py`, `checkpointer.py` |
| `DB_POOL_SIZE` | No | `5` | `connection.py` |
| `DB_MAX_OVERFLOW` | No | `10` | `connection.py` |
| `DB_POOL_TIMEOUT` | No | `30` | `connection.py` |
| `DB_ECHO` | No | `false` | `connection.py` (SQLAlchemy echo) |

---

## Test Responsibilities

You own `tests/infrastructure/`. Current suite in `test_connection.py`:
- `test_session_commit_and_rollback` — transactional integrity
- `test_pool_health_check` — `SELECT 1` via engine
- `test_checkpointer_setup_idempotent` — double-init safety
- `test_campaign_insert_unique_thread_id` — `IntegrityError` on duplicate `thread_id`
- `test_campaign_start_endpoint_round_trip` — full HTTP POST → GET via `httpx.ASGITransport`

All tests skip gracefully when `DATABASE_URL` is not set.

---

## Current Phase: 3 (V3.1)

From ROADMAP.md — active infrastructure-relevant items:
- [ ] **Semantic Memory:** Implement pgvector to give agents long-term "wisdom" across campaigns
- [ ] **Cost Optimization:** Token-usage monitoring (may need new tables)
- [ ] **RAG Pipeline Test:** Validate storage quality and retrieval performance (see `RAG_TEST.md`)

---

## When You're Lost

1. Read this file
2. Read `CONTRACTS.py` (the single source of truth for data shapes)
3. Read `AGENCY_PROTOCOLS.md §4.3` (state persistence contract)
4. Read `BRIDGE_SPEC.md §4` (state re-hydration protocol)
5. Check `tests/infrastructure/test_connection.py` for working examples
