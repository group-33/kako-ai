"""Endpoints for demand-analysis workflows."""
import dspy
from fastapi import APIRouter, Depends, Request

from backend.src.demand_analysis.agent import DemandAnalystAgent
from backend.src.demand_analysis.models import (
    DemandAnalysisRequest,
    DemandAnalysisResponse
)

router = APIRouter(prefix="/demand", tags=["demand"])


def get_demand_analyst_agent(request: Request) -> DemandAnalystAgent:
    agent = getattr(request.app.state, "demand_analyst_agent", None)
    if agent is None:
        raise RuntimeError("Demand analyst agent not initialized.")
    return agent


@router.post("/analysis", response_model=DemandAnalysisResponse)
def analyze_demand(
    payload: DemandAnalysisRequest,
    agent: DemandAnalystAgent = Depends(get_demand_analyst_agent),
) -> DemandAnalysisResponse:
    """Run the Demand Analyst agent using the provided request/BOM context."""
    result: dspy.Prediction = agent(
        user_request=payload.user_query,
        bom=payload.bom,
        quantity_required=payload.quantity_required,
    )
    return DemandAnalysisResponse(process_result=result.process_result)
