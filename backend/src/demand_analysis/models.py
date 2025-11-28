"""Pydantic models for demand-analysis workflows."""
from typing import List, Optional, Literal

from pydantic import BaseModel, Field

from backend.src.models import BillOfMaterials


class MissingComponent(BaseModel):
    """Represents a component that is not currently available in full quantity."""
    part_number: str = Field(description="Identifier of the part that is short on stock.")
    quantity_needed: int = Field(description="Quantity still needed to meet the request.")
    quantity_in_stock: int = Field(description="Currently available quantity for this part.")
    estimated_delivery_days: Optional[int] = Field(
        default=None,
        description="Estimated days until replenishment, when known."
    )


class FeasibilityAnalysis(BaseModel):
    """Structured response returned by the Demand Analyst."""
    status: Literal["available", "partial", "unavailable"] = Field(
        description="Overall availability assessment for the requested quantity."
    )
    analysis_summary: str = Field(description="Narrative summary of the analysis and key findings.")
    lacking_materials: List[MissingComponent] = Field(
        description="List of parts that are insufficient or missing."
    )


class DemandAnalysisRequest(BaseModel):
    """Input payload expected by the Demand Analyst agent."""
    user_query: str = Field(
        description="User request to analyze (e.g., feasibility, availability, or deliveries)."
    )
    bom: Optional[BillOfMaterials] = Field(
        default=None,
        description="Bill of Materials context for the request, when available."
    )
    quantity_required: int = Field(
        default=1,
        description="Number of finished units the user wants to fulfill."
    )


class DemandAnalysisResponse(BaseModel):
    """Response produced by the Demand Analyst agent."""
    process_result: str = Field(description="Natural-language summary produced by the agent.")
