# KakoAI 🤖

AI-powered copilot that automates critical workflows, enables detailed feasibility projections,
and assists in finding optimal procurement options.

> [!TIP]
> **Watch our Demo Video:** [Link to Video (Placeholder)](https://youtube.com)

## Getting Started (University Project Evaluation)

This section guides evaluators through the core functionality of KakoAI using our mock user. Since this is a university project connected to real industrial data, some features are simulated to protect sensitive information and avoid API costs.

**Live Deployment:** [https://kakoai.de/](https://kakoai.de/)

### 1. Login with Mock Credentials

Please use the following credentials to access the evaluation environment. This account has access to cached data.

| Role          | Email            | Password            |
| :------------ | :--------------- | :------------------ |
| **Evaluator** | `add email here` | `add password here` |

> [!IMPORTANT]
> **Data Privacy & Caching:** The "Mock User" operates in a restricted environment. BOM extractions are processed live (using Gemini 2.5), but **pricing and inventory data will return cached/mocked responses** to prevent live API charges and ensure GDPR compliance for non-NDA users.

### 2. Available Test Data

We have provided sample technical drawings in the `test_boms/` directory of this repository. These files are compatible with our extraction pipeline.

- `test_boms/Test_BOM_PDF1.pdf`
- `test_boms/Test_BOM_PDF2.pdf`
- `test_boms/Test_BOM_PNG.png`

### 3. Core Workflows

For a detailed guide, please refer to the **User Guide** in `report/1_user-guide.pdf`.

#### A. Extracting a Bill of Materials (BOM)

1. Go to the **Dashboard** or **New Chat**.
2. Click the paperclip icon 📎 and upload a file from `test_boms/`.
3. Ask the agent: _"Extract the BOM from this drawing"_ (or use the Quick Action).
4. The **BOM Editor** will appear. Review the extracted data and click "Confirm" to save it to conversation state.

#### B. Feasibility & Procurement

Once a BOM is in context (or if you ask generally):

- **Feasibility:** Ask _"Can we build 500 units of this?"_. The agent will check (mocked) Xentral ERP inventory.
- **Procurement:** Ask _"Find the best price for these parts"_. The agent will query (cached) Nexar API data for pricing.

---

## 🛠️ Technical Documentation

For an in-depth architectural overview, please refer to our **Management Report** in `report/2_management-report.pdf`.

### Technology Stack

The system is built on a modern, decoupled architecture designed for scalability and industrial usage.

| Component        | Technology              | Description                                       |
| :--------------- | :---------------------- | :------------------------------------------------ |
| **Frontend**     | React + Vite            | Component-based UI with fast build tooling.       |
| **Styling**      | Tailwind CSS + Radix UI | Utility-first styling with accessible primitives. |
| **State**        | Zustand                 | Scalable client-side state management.            |
| **Backend**      | FastAPI (Python)        | High-performance async API.                       |
| **Agentic Core** | DSPy + Gemini           | Declarative framework for programming LLMs.       |
| **Vision**       | OpenCV                  | Image preprocessing for BOM extraction.           |
| **Database**     | Supabase                | Auth & persistent storage.                        |
| **Integrations** | Xentral ERP + Nexar API | Enterprise resource planning & market data.       |

### Key Features

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
