"""Pydantic models for demand-analysis tools (inventory and feasibility)."""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


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
    """Structured feasibility analysis response."""
    status: Literal["available", "partial", "unavailable"] = Field(
        description="Overall availability assessment for the requested quantity."
    )
    analysis_summary: str = Field(description="Narrative summary of the analysis and key findings.")
    lacking_materials: List[MissingComponent] = Field(
        description="List of parts that are insufficient or missing."
    )
