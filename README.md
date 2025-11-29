# KakoAI 🤖

AI-powered copilot that automates critical workflows, enables detailed feasibility projections, 
and assists in finding optimal procurement options.

## Repository Guidelines

### Backend Layout

```
.
├── backend/
│   └── src/
│       ├── main.py       # FastAPI entrypoint (uvicorn backend.src.main:app --reload)
│       ├── agent.py      # ReAct agent wiring available tools
│       ├── tools/        # Tool modules exposed to the agent (e.g., BOM extraction)
│       ├── config.py     # Env-driven config (LLM keys, Xentral settings)
│       └── models.py     # Shared data shapes
├── .env                  # Local environment variables (gitignored)
└── requirements.txt      # Runtime dependencies (FastAPI, uvicorn, DSPy, etc.)
```

### Develop & Run

- Install dependencies into your virtualenv: `pip install -r requirements.txt`.
- From the repo root, start the API: `uvicorn backend.src.main:app --reload`.
- Visit Swagger UI at `http://127.0.0.1:8000/docs`.

### API Surface (current)

- `POST /agent/run` – ReAct agent entrypoint. Send form field:
  - `user_query` (str, required)

The agent currently exposes a BOM extraction tool that expects a local file path string; file upload handling is not yet wired into this endpoint.
