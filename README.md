# KakoAI 🤖

AI-powered copilot that automates critical workflows, enables detailed feasibility projections, 
and assists in finding optimal procurement options.

## Layout

```
.
├── backend/
│   └── src/
│       ├── main.py        # FastAPI entrypoint
│       ├── agent.py       # DSPy ReAct agent wiring + tool registry
│       ├── models.py      # Pydantic request/response + shared models
│       ├── utils.py       # Response builders + trajectory parsing + BOM merge helpers
│       └── tools/         # Agent tools (BOM extraction, demand analysis, procurement)
└── frontend/
    └── src/
        └── components/
            ├── Chat.tsx             # Calls backend /agent per user message
            └── tools/
                ├── BOMTableTool.tsx
                └── ProcurementOptionsTool.tsx
```

## Run Locally

Backend:
- `pip install -r requirements.txt`
- `uvicorn backend.src.main:app --reload`

Frontend:
- `cd frontend && npm install`
- `npm run dev`

## API

- `GET /health` – health check.
- `POST /agent` – unified agent endpoint.
  - JSON: `{ "user_query": "...", "thread_id": "..." }`
  - Optional BOM confirmation: `{ "bom_update": { "bom_id": "...", "overrides": [{ "item_id": "...", "quantity": 1 }] } }`
  - Returns an `AgentResponse` with `blocks` (`text` and `tool_use`) that the frontend renders.

## BOM Workflow (MVP)

- Send a message that includes a drawing path ending in `.png`, `.jpg`, `.jpeg`, or `.pdf` to trigger BOM extraction.
- The backend returns a `display_bom_table` tool block with:
  - `rows[]` (each row has a stable `id` derived from non-editable extraction fields)
  - `bom_id` (revision id) and `thread_id` (chat thread)
- Edit quantities and click **Bestätigen**; the frontend sends `bom_update` to `/agent`.
- The backend validates `bom_id`, merges overrides into the stored BOM for that `thread_id`, and stores the confirmed BOM for subsequent calls.

## Configuration

- Create a `.env` (gitignored) with at least `GOOGLE_API_KEY` for the Gemini-backed LLM.
- Optional integrations:
  - SSH file lookup for drawings: `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PASS`, `REMOTE_DIR`
  - Procurement (Nexar): `NEXAR_CLIENT_ID`, `NEXAR_CLIENT_SECRET`
  - ERP/DB tooling (Xentral/Supabase): `XENTRAL_API_KEY`, `XENTRAL_BASE_URL`, `SUPABASE_PASSWORD`
