# KakoAI - Backend

FastAPI service that hosts the DSPy ReAct agent, tool registry, and model selection.

## 🚀 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Agent Framework**: [DSPy](https://dspy.ai/) (ReAct logic + Signatures)
- **LLM Provider**: Google Vertex AI (Gemini 2.5 Flash/Pro)
- **Tooling**: Pydantic, Dotenv

## 📂 Project Structure

```
backend/
└── src/
    ├── tools/         # Agent tools (BOM extraction, Procurement, Analysis)
    ├── agent.py       # Main ReAct agent wiring & tool registry
    ├── config.py      # App configuration & Model definitions (Vertex)
    ├── main.py        # FastAPI entrypoint (Agent, Title, Config)
    ├── models.py      # Pydantic models (Requests, Responses, BOM)
    └── utils.py       # Helper functions (Trajectory parsing, BOM merging)
```

## 🛠️ Run Locally

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Server**:
   ```bash
   uvicorn backend.src.main:app --reload
   ```

## 🔌 API Reference

### Agent & Chat
- `POST /agent`: Core endpoint to run the ReAct agent.
  - **Payload**:
    ```json
    {
      "user_query": "Check feasibility for 500 units...",
      "thread_id": "optional-uuid",
      "model_id": "gemini-2.5-flash"
    }
    ```
  - **BOM Confirmation** (optional): `{ "bom_update": { ... } }`
  - **Returns**: `AgentResponse` with UI-renderable blocks.

- `POST /chat/title`: Generates a thread title from the first message.
  - **Payload**: `{ "user_query": "...", "model_id": "..." }`
  - **Returns**: `{ "title": "Feasibility Report 500u" }`

### Configuration
- `GET /config/models`: Returns list of available Vertex models.
  - **Returns**: `{ "models": [{ "id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", ... }] }`

### System
- `GET /health`: Simple health check.

## ⚙️ Configuration

The app relies on environment variables and a service account file.

- **Vertex AI auth**: Place your service account JSON at `backend/src/kako-ai_auth.json`.
- **Project Config**: Defined in `backend/src/config.py`.
- **Environment Variables** (`.env`):
  - `SSH_HOST`, `SSH_USER`, ... (for Drawing lookup)
  - `NEXAR_CLIENT_ID` / `SECRET` (for Procurement)
  - `XENTRAL_API_KEY` (for ERP)
