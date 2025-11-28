"""FastAPI application bootstrap."""
import dspy
from fastapi import FastAPI

from backend.src.bom_extraction.perform_extraction import BOMExtraction
from backend.src.config import GEMINI_2_5_PRO
from backend.src.demand_analysis.agent import DemandAnalystAgent
from backend.src.routers import bom, demand

# --- Configure LLM globally ---
dspy.configure(lm=GEMINI_2_5_PRO)

app = FastAPI(title="KakoAI")

# Instantiate agents once and store on app state for DI access
app.state.bom_extractor = dspy.Predict(BOMExtraction)
app.state.demand_analyst_agent = DemandAnalystAgent()

app.include_router(bom.router)
app.include_router(demand.router)


@app.get("/health")
def service_health() -> dict:
    """Health check endpoint."""

    return {"status": "healthy", "message": "KakoAI API is up and running"}

# Run with: uvicorn backend.src.main:app --reload
