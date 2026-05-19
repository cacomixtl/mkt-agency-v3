# Market Beez (mkt-agency-v3)

## Overview
**Market Beez** is an autonomous, multi-agent AI Marketing Agency. The system operates on a strictly decoupled architecture, featuring a **FastAPI** backend that orchestrates a LangGraph swarm (powered by Gemini 2.5), and a **Vite/React TypeScript** frontend known as the "Director's Cockpit" for real-time monitoring and Human-in-the-Loop (HITL) approvals. 

Additionally, a parallel **WhatsApp integration** acts as a secondary, lightweight interface for handling critical or minimal HITL inputs on the go.

## Architecture Boundaries

- **FastAPI Core (`main_v3.py`)**: The asynchronous backbone handling REST endpoints, SSE streams, and WhatsApp webhooks.
- **LangGraph Swarm (`/logic`)**: The intelligence layer featuring a Supervisor pattern that routes briefs to specialized Worker Agents (Creative, Judge, etc.).
- **Director's Cockpit (`/ui`)**: An isolated React frontend for rich visual monitoring of agent reasoning, state visualization, and content approval.
- **Persistence (`/infrastructure`)**: All multi-agent thread states are durably serialized into PostgreSQL via an `AsyncPostgresSaver`, ensuring perfect resilience across restarts.

## Setup & Environment Variables

1. Create a `.env` file in the root directory:
```env
# Core API Keys
GOOGLE_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash

# FinOps / Development
AGENCY_MOCK_LLM=true # Set to 'true' to bypass API costs during UI development

# WhatsApp API (Secondary Interface)
WHATSAPP_ACCESS_TOKEN=your_token
PHONE_NUMBER_ID=your_waba_phone_id
VERIFY_TOKEN=your_webhook_verify_token
APP_SECRET=your_meta_app_secret

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/marketing_agent
```

2. Boot the Backend:
```bash
python -m venv .venv
source .venv/bin/activate  # Or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt

uvicorn main_v3:app --reload --port 8000
```

3. Boot the Frontend Cockpit:
```bash
cd ui
npm install
npm run dev
```

## Deployment
The backend is containerized via a root `Dockerfile` and configured for seamless deployment on **Railway** (see `railway.toml`). The Vite frontend is compiled and deployed separately to maintain strict CI/CD boundaries.
