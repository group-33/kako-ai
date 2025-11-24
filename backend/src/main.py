"""FastAPI application bootstrap."""
from fastapi import FastAPI
import dspy

from backend.src.routers import bom
from backend.src.config import GEMINI_2_5_PRO

# --- Configure LLM globally ---
dspy.configure(lm=GEMINI_2_5_PRO)

app = FastAPI(title="KakoAI")
app.include_router(bom.router)


@app.get("/health")
def service_health() -> dict:
    """Health check endpoint."""

    return {"status": "healthy", "message": "KakoAI API is up and running"}

# Run with: uvicorn src.main:app --reload
