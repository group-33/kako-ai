"""FastAPI application bootstrap."""
from fastapi import FastAPI

from src.routers import bom

app = FastAPI(title="KakoAI")
app.include_router(bom.router)


@app.get("/health")
def service_health() -> dict:
    """Health check endpoint."""

    return {"status": "healthy", "message": "KakoAI API is up and running"}

# Run with: uvicorn src.main:app --reload
