# 🗺️ Project Roadmap: Market Beez (mkt-agency-v3)

**Vision:** To build a resilient, autonomous Marketing Agency that operates with strict brand consistency. The agency is a swarm of specialized LangGraph agents that collaborate to create and evaluate marketing content. Operations are overseen by a Human-in-the-Loop (HITL) system via a rich web Cockpit, with WhatsApp serving as a lightweight fallback for critical approvals.

### Version History
*   **Version 1.0.0:** Monolith_Mkt_Agent (Legacy WhatsApp Bot)
*   **Version 2.0.0:** agency_v2 (Inline Refactors)
*   **Version 3.0.0:** mkt-agency-v3 (Current Live Architecture - Decoupled React/FastAPI)

---

## 📍 Current Status: Phase 3 (V3.1 Iteration)
*   **Stability:** Beta / Production-Ready
*   **Focus:** Logic Refinement, UI UX Polish, and Semantic Optimization
*   **Deployment Platform**: Railway

---

## 🏁 Phase 1: Foundation & Reliability (Completed)
*Goal: Move from a local prototype to a production-ready persistent system.*
- [x] **Database Migration:** Transition from in-memory dicts to PostgreSQL.
- [x] **Checkpointer Implementation:** Integrate `AsyncPostgresSaver` for thread resilience.
- [x] **Contract Enforcement:** Standardize all agent inputs/outputs via Pydantic (`CONTRACTS.py`).

## 🏁 Phase 2: Orchestration & Scaling (Completed)
*Goal: Refine the "Swarm" logic and improve operator transparency.*
- [x] **Supervisor Pattern:** Move from linear chains to a Manager-Worker swarm architecture.
- [x] **Director’s Cockpit:** Launch the decoupled Vite/React UI with real-time SSE streaming.
- [x] **Human-in-the-loop (HITL):** Integrate breakpoint approvals via the Cockpit and WhatsApp.
- [x] **FinOps Guardrails:** Implement `AGENCY_MOCK_LLM` for zero-cost UI iteration.

## 🚀 Phase 3: Intelligence & Optimization (V3.1 - Current Focus)
*Goal: Deepen the swarm's reasoning capabilities and polish the UI experience.*
- [ ] **Agent Logic Evolution:** Refine the Creative and Judge prompts for deeper brand philosophy adherence. Implement dynamic few-shot learning.
- [ ] **Cockpit Polish:** Enhance the UI animations, error boundary surfacing, and mobile responsiveness of the React dashboard.
- [ ] **Semantic Memory:** Implement `pgvector` to give agents long-term project "wisdom" and context across multiple campaigns.
- [ ] **Cost Optimization:** Token-usage monitoring and automated model switching (A2A) based on task complexity.

## 🔭 Phase 4: Expansion (Future)
*Goal: Multi-channel dominance.*
- [ ] **Multi-Platform Publishing:** Expand from Instagram/Threads to LinkedIn and X via Graph APIs.
- [ ] **A/B Testing Swarms:** Allow the manager to spawn parallel creative teams and automatically judge the winning draft.

---

## 🛑 Out of Scope (For Now)
*   Native Mobile Application.
*   Real-time video generation.
*   Direct client-facing billing portal.

---

## 📜 Completed Milestones
- **17/03/2026**: Successfully deployed V1 Monolith to WhatsApp. 
- **15/05/2026**: Deployed V3 Architecture to Railway, separating FastAPI backend and React frontend. Integrated `AsyncPostgresSaver` for true HITL resilience.
