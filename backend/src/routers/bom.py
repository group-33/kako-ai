"""Endpoints for BOM-related workflows."""
from fastapi import APIRouter

router = APIRouter(prefix="/bom", tags=["bom"])


@router.get("/health")
def bom_router_health() -> dict:
    """Placeholder endpoint proving the router wiring."""

    return {"status": "ok"}
