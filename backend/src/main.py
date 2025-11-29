"""FastAPI entrypoint exposing the unified KakoAI agent."""
import dspy
from fastapi import FastAPI, Depends, Form, Request

from backend.src.config import GEMINI_2_5_PRO
from backend.src.agent import KakoAgent

# --- Configure LLM globally ---
dspy.configure(lm=GEMINI_2_5_PRO)

app = FastAPI(title="KakoAI")

# Instantiate the unified agent once and store on app state for DI access
app.state.agent = KakoAgent()


def get_agent(request: Request) -> KakoAgent:
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        print("Agent not initialized, creating new instance..")
        agent = KakoAgent()
        request.app.state.agent = agent
    return agent


@app.post("/agent")
async def run_agent(
    user_query: str = Form(..., description="Natural language request to complete."),
    agent: KakoAgent = Depends(get_agent),
):
    return agent(user_query=user_query)

@app.get("/health")
def service_health() -> dict:
    """Health check endpoint."""

    return {"status": "healthy", "message": "KakoAI API is up and running"}

# Run with: uvicorn backend.src.main:app --reload
