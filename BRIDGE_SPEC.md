This document serves as the formal "Interface Control" for **Agency V3**. It defines how the **Python/FastAPI Brain** communicates with the **TypeScript/React Face**. This bridge is the source of truth for both the **Logic Architect** and the **UI/UX Specialist**.

---

## **1\. The Handshake (Type Safety)**

To prevent the frontend and backend from drifting apart, we enforce **strict type parity**.

* **Source of Authority:** `CONTRACTS.py` (Python Pydantic Models). See `§5: API Contracts` for all typed request/response models.  
* **Synchronization:** The UI Specialist will use a schema generator to produce a matching `types.ts` file.  
* **The Envelope:** All API responses must use the `APIEnvelope` model from `CONTRACTS.py`:

JSON  
{  
  "status": "success | error",  
  "data": {},  
  "meta": {  
    "thread\_id": "string",  
    "timestamp": "ISO-8601",  
    "version": "v3.0.0"  
  }  
}

---

## **2\. The Command Map (REST Endpoints)**

These are the standard "Pull" interactions used for configuration and explicit actions.

| Endpoint | Method | Purpose | Contract Model |
| :---- | :---- | :---- | :---- |
| /campaign/start | POST | Initializes a new thread | `CampaignStartRequest` → `APIEnvelope` |
| /campaign/{id}/state | GET | Fetches the full current state (incl. `CampaignStage`) | `APIEnvelope` with `V3AgencyState` data |
| /campaign/{id}/resume | POST | Submits HITL approval/feedback | `CampaignResumeRequest` → `APIEnvelope` |
| /campaign/{id}/cancel | POST | Terminates the current swarm run | `APIEnvelope` |

---

## **3\. The Event Stream (SSE Protocol)**

Since agent cycles are asynchronous and time-consuming, we use **Server-Sent Events (SSE)** to provide real-time transparency in the Director's Cockpit.

**Endpoint:** GET /campaign/{id}/stream

### **Event Dictionary**

The UI must listen for the following event types to update the "Thinking" state.  
All event models are defined as typed Pydantic classes in `CONTRACTS.py §5` (`SSEEvent` union):

* **node\_start** (`SSEEventNodeStart`): Sent when a specific agent begins work.  
  * *Payload:* `{"event_type": "node_start", "node_name": "string"}`  
* **agent\_thought** (`SSEEventAgentThought`): Real-time streaming of agent reasoning.  
  * *Payload:* `{"event_type": "agent_thought", "text": "string", "step": "integer"}`  
* **breakpoint** (`SSEEventBreakpoint`): Graph paused for Director intervention.  
  * *Payload:* `{"event_type": "breakpoint", "approval_mode": "active|passive", "preview": MarketingContent}`  
* **completion** (`SSEEventCompletion`): Campaign finalized.  
  * *Payload:* `{"event_type": "completion", "stage": CampaignStage, "publish_targets": [...]}`  
* **error** (`SSEEventError`): Processing error occurred.  
  * *Payload:* `{"event_type": "error", "error_code": int, "message": "string"}`

---

## **4\. State Re-Hydration & Resilience**

Because the system is backed by the **Postgres Checkpointer**, the bridge supports "Instant Recovery."  
The re-hydrated state is a `V3AgencyState` (defined in `CONTRACTS.py §4`), which includes the full `CampaignStage` lifecycle and `revision_history` audit trail.

1. **Thread Persistence:** The UI stores the active thread\_id in localStorage.  
2. **Re-Hydration Flow:** On page refresh, the React app calls `GET /campaign/{id}/state`. The Backend retrieves the latest `V3AgencyState` snapshot from PostgreSQL.  
3. **UI Sync:** The React state is updated to match the `V3AgencyState.stage` and active node, ensuring no loss of perceived continuity.

---

## **5\. Error & Guardrail Protocol**

When an agent hits a wall, the bridge must communicate the failure gracefully.

| Error Code | Logic Meaning | UI Action |
| :---- | :---- | :---- |
| 422 Unprocessable Entity | Pydantic validation failed | Show "Data Mismatch" warning. |
| 429 Too Many Requests | LLM Provider Rate Limit | Show "Cooling Down" countdown. |
| 409 Conflict | Aesthetic Drift (Judge rejected 3x) | Show "Manual Revision Required" dialog. |
| 503 Service Unavailable | Database/Infrastructure failure | Show "Offline" status indicator. |

---

## **6\. Security & Handshake (CORS)**

* **Origin Locking:** The FastAPI backend will only accept requests from the specific Railway URL assigned to the React Frontend.  
* **Header Requirements:** Every request must include the X-Thread-ID header for tracking and the Authorization: Bearer \[API\_KEY\] for access control.

---

### **🛡️ The "Wildcard" Safety Rule**

**Debug Mode:** The bridge includes a header X-Agency-Debug: true. When active, the backend includes the raw LLM prompts and full JSON stack traces in the SSE stream, allowing the UI Specialist to debug the "Brain" directly from the browser console.

