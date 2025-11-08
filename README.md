# KakoAI 🤖

AI-powered copilot that automates critical workflows, enables detailed feasibility projections, 
and assists in finding optimal procurement options.

## Repository Guidelines

### Project Layout

```
.
├── src/                      # Python package with all application code
│   ├── main.py               # FastAPI entrypoint (run via uvicorn src.main:app --reload)
│   ├── config.py             # Scratchpad for shared config constants (e.g., model IDs)
│   ├── models.py             # Pydantic BaseModel definitions for agent IO
│   └── routers/              # FastAPI routers grouped by domain
│       └── bom.py            # Example BOM router with /bom/health
├── .env                      # Local environment variables for secrets and API keys
└── requirements.txt          # Runtime dependencies (FastAPI, uvicorn, pydantic, etc.)
```

### Develop & Run

- Install dependencies into your virtualenv: `pip install -r requirements.txt`.
- Start the API locally: `uvicorn src.main:app --reload` (currently serves `/health` and `/bom/health`).
- Add new endpoints by creating routers under `src/routers/` and including them in `src/main.py`.

### Conventions

- Create a subfolder under `src/` for each KakoAI functionality.
- Define shared configuration nuggets (e.g., LLM names) in `src/config.py`.
- Use Pydantic models within `src/models.py` to document agent inputs/outputs before wiring implementations.