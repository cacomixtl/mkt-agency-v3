## Overview


# 🗺️ Project Roadmap: [Market Beez]

**Vision:** To build a resilient, autonomous [Marketing Agency] that operates with [Primary Aesthetic/Goal].  The agency is a swarm of agents that work together to create and publish marketing content. The agency is a monolith that is deployed as a single unit + a Human-in-the-loop (HITL) system that allows the user to approve or reject the content. 

Version 1.0.0 (Monolith_Mkt_Agent)  
Version 2.0.0 (agency_v2, within Version 1.0.0 files) 
Version 3.0.0 (Current scope of development)


---

## 📍 Current Status: Phase 1 (Core Infrastructure)
*   **Stability:** Alpha
*   **Focus:** State Persistence & Multi-Agent Communication
*   **Deployment Platform**: Railway
*   **Specific API**: Meta's Graph API (WhatsApp, Instagram & Threads)

---

## 🚀 Phase 1: Foundation & Reliability (Current)
*Goal: Move from a local prototype to a production-ready persistent system.*

- [ ] **Database Migration:** Transition from in-memory dicts to PostgreSQL.
- [ ] **Checkpointer Implementation:** Integrate `AsyncPostgresSaver` for thread resilience.
- [ ] **Contract Enforcement:** Standardize all agent inputs/outputs via Pydantic.
- [ ] **Automated Evals:** Implement a basic "Gold Standard" test for the primary agent loop.

## 🏗️ Phase 2: Orchestration & Scaling (Next 1-3 Months)
*Goal: Refine the "Swarm" logic and improve operator transparency.*

- [ ] **Supervisor Pattern:** Move from linear chains to a Manager-Worker swarm architecture.
- [ ] **Dynamic Routing:** Implement fallbacks for external API failures.
- [ ] **Director’s Cockpit:** Launch the FastAPI-streamed UI for real-time monitoring.
- [ ] **Human-in-the-loop (HITL):** Integrate breakpoint approvals via [Platform, e.g., WhatsApp/Web].

## 🔭 Phase 3: Intelligence & Optimization (Future)
*Goal: Enhance the "soul" of the agency and reduce operational costs.*

- [ ] **Semantic Memory:** Implement `pgvector` for long-term project "wisdom."
- [ ] **Cost Optimization:** Token-usage monitoring and automated model switching (A2A).
- [ ] **Multi-Platform Support:** Expand from [Platform A] to [Platform B].

---

## 🛑 Out of Scope (For Now)
*   Native Mobile Application.
*   Real-time video generation.
*   Direct client-facing billing portal.

---

## 📜 Completed Milestones
- **17/03/2026**: Successfully deployed V1 Monolith to [Platform]. 
- **17/03/2026**: Integrated basic [Specific API].  
