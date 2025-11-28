# KakoAI 🤖

AI-powered copilot that automates critical workflows, enables detailed feasibility projections, 
and assists in finding optimal procurement options.

## Repository Guidelines

### Project Layout

```
.
├── backend/
│   └── src/
│       ├── main.py                 # FastAPI entrypoint (uvicorn backend.src.main:app --reload)
│       ├── config.py               # Env-driven config (LLM keys, Xentral settings)
│       ├── models.py               # Shared data shapes
│       ├── bom_extraction/         # BOM extraction feature module
│       ├── demand_analysis/        # Demand analysis feature module
│       └── routers/                # FastAPI routers by domain
│           ├── bom.py              # /bom/extract
│           └── demand.py           # /demand/analysis
├── .env                            # Local environment variables (gitignored)
└── requirements.txt                # Runtime dependencies (FastAPI, uvicorn, DSPy, etc.)
```

### Develop & Run

- Install dependencies into your virtualenv: `pip install -r requirements.txt`.
- From the repo root, start the API: `uvicorn backend.src.main:app --reload`.
- Visit Swagger UI at `http://127.0.0.1:8000/docs`.
- Add new endpoints by creating routers under `backend/src/routers/` and including them in `backend/src/main.py`.

### Conventions

- Create a subfolder under `backend/src/` for each KakoAI functionality.
- Define shared configuration nuggets (e.g., LLM names) in `backend/src/config.py`; load secrets via `.env`.
- Use feature-local models in their packages (`bom_extraction/models.py`, `demand_analysis/models.py`); keep any shared shapes in `backend/src/models.py`.

### API Surface (current)

- `GET /health` – service health.
- `POST /bom/extract` – multipart file upload (`file`) for a drawing; returns `BOMExtractionResponse` with an extracted BOM.
- `POST /demand/analysis` – demand analyst agent; body `DemandAnalysisRequest` with optional BOM, returns natural-language `process_result`.
