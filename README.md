# MarketBot (AI Marketing Agent)

## Overview
This is a **Modular Monolith** backend for an AI Marketing Agent delivered entirely via WhatsApp. It is built natively on **FastAPI** to directly receive WhatsApp Webhooks, orchestrate the LangGraph ReAct Agent (using Gemini 2.5), generate images, and publish to the Instagram Graph API.

> Note: Early versions of this documentation referenced `n8n` as an orchestrator. **This project is now a standalone native FastAPI implementation**; n8n is no longer required or used, drastically reducing latency and complexity.

## Setup & Environment Variables

1. Create a `.env` file in the root directory:
```env
# Core API Keys
GOOGLE_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash

# WhatsApp API
WHATSAPP_ACCESS_TOKEN=your_token
PHONE_NUMBER_ID=your_waba_phone_id
VERIFY_TOKEN=your_webhook_verify_token
APP_SECRET=your_meta_app_secret

# Instagram API
META_APP_ID=your_meta_id
META_APP_SECRET=your_meta_secret
INSTAGRAM_ACCOUNT_ID=ig_account
INSTAGRAM_ACCESS_TOKEN=ig_token

# Database
# The stack must support pgvector.
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/marketing_agent
```

2. Run Locally with Uvicorn:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload
```

## WhatsApp Webhook Configuration

To receive messages from users, configure your Meta App's Webhook to point to your deployed instance:

### Webhook URL
`https://your-domain.com/webhook`

**Subscribed Fields:**
- `messages` (Required for text, audio, and image messages)

## Architecture

- **FastAPI**: Core async web framework routing webhooks.
- **LangGraph**: Orchestrates the ReAct Agent logic and tools.
- **SQLModel / PostgreSQL**: Storage for Users, Campaigns, and pgvector embeddings for RAG.
- **APScheduler**: Manages deferred/scheduled Instagram publishing.





