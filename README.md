# KakoAI 🤖

AI-powered copilot that automates critical workflows, enables detailed feasibility projections, 
and assists in finding optimal procurement options.

## Key Features

- **ReAct Agent**: Powered by DSPy + Gemini (Vertex AI).
- **Generative UI**: Renders interactive BOM tables and analysis tools.
- **Full Persistence**: Chat history and user sessions are persisted locally.
- **Authentication**: Client-side auth with user profiles.
- **Internationalization**: Full English/German support.
- **Dynamic Configuration**: Switch models on the fly.
- **Draft Quick Actions**: Dashboard actions open localized draft prompts before sending.

## Layout

```
.
├── backend/
│   └── src/
│       ├── main.py        # FastAPI entrypoint (Agent + Title + Config APIs)
│       ├── agent.py       # DSPy ReAct agent wiring + tool registry
│       ├── config.py      # App configuration & Model definitions
│       ├── models.py      # Pydantic request/response models
│       ├── utils.py       # Tool adapters + BOM/procurement helpers
│       └── tools/         # Agent tools (BOM extraction, demand analysis, procurement)
└── frontend/
    └── src/
        ├── components/    # UI Components & Generative Tools
        ├── pages/         # Login, Profile, Chat, Config Pages
        ├── runtime/       # Backend connection & Persistence logic
        ├── store/         # State Management (Zustand)
        ├── i18n.ts        # Localization bootstrapping
        └── locales/       # Localization strings
```

## Run Locally

**Backend:**
```bash
pip install -r requirements.txt
uvicorn backend.src.main:app --reload
```

**Frontend:**
```bash
cd frontend && npm install
npm run dev
```

## API Overview

### Agent & Chat
- `POST /agent`: Unified agent endpoint.
  - Payload: `{ "user_query": "...", "thread_id": "...", "model_id": "..." }`
  - Returns: Streamable/Block-based agent response.
- `POST /chat/title`: Generates a concise title for a new thread.
  - Payload: `{ "user_query": "...", "model_id": "..." }`

### Configuration
- `GET /config/models`: Returns list of available LLMs.

### System
- `GET /health`: Health check.

## Configuration

- Create a `.env` (gitignored) with your Vertex credentials (see below).
- Optional integrations:
  - SSH file lookup for drawings: `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PASS`, `REMOTE_DIR`
  - Procurement (Nexar): `NEXAR_CLIENT_ID`, `NEXAR_CLIENT_SECRET`
  - ERP/DB tooling (Xentral/Supabase): `XENTRAL_API_KEY`, `SUPABASE_PASSWORD`

### Vertex / Gemini Setup
- Place your service account JSON at `backend/src/kako-ai_auth.json`, or update `GOOGLE_APPLICATION_CREDENTIALS`.
- Project/region are defined in `backend/src/config.py` (`project: kako-ai-480517`, `vertex_location: europe-west1`).
