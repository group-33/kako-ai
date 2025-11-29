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
│       ├── tools/        # Tool modules exposed to the agent
│       │   ├── bom_extraction/    # BOM extraction tool
│       │   └── demand_analysis/   # Demand analysis tools
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

- `GET /health` – service health.
- `POST /agent` – ReAct agent entrypoint. Send form field:
  - `user_query` (str, required)

Tools available to the agent:
- BOM extraction (`bom_extraction/bom_tool.py`): expects a local file path string for an image.
- Demand analysis (`demand_analysis/`): inventory context helpers and a structured feasibility check.

Note: File upload handling for BOM extraction is not yet wired into the API; the agent cannot read uploaded files directly.
