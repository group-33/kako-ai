"""Pydantic models that define the agent IO contracts."""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class BOMItem(BaseModel):
    part_number: str = Field(description="Pos. number")
    quantity: int = Field(description="The total number of this component required.")
    description_of_part: str = Field(description="A brief description of the component.")
    no_of_poles: int = Field(description="Number of Poles. No. of poles field")
    order_number: int = Field(description="The order number.")
    hdm_no: int = Field(description="HDM no.")
    measurments_in_discription: str = Field(description="Measurements included in the description.")

class BillOfMaterials(BaseModel):
    items: List[BOMItem] = Field(description="A list of all items found in the Bill of Materials.")
    # bom_extractor.py (continued...)

class BOMExtractionRequest(BaseModel):
    """Input expected by the BOM extractor agent."""

    # TODO


class BOMExtractionResponse(BaseModel):
    """Response shared with downstream agents."""

    bom: BillOfMaterials = Field(description="The extracted Bill of Materials.")


# --- Models for Demand-Analyst Agent ---

class DemandAnalysisRequest(BaseModel):
    """Input payload expected by the Demand Analyst agent."""

    bom: Optional[BillOfMaterials] = Field(
        default=None,
        description="Bill of Materials context for the request (if applicable)."
    )
    user_query: str = Field(description="Original user request.")
    quantity_required: int = Field(default=1, description="Units requested by the user.")


class LackingMaterial(BaseModel):
    """Represents a component that is not currently available in full quantity."""

    part_number: str
    quantity_needed: int
    quantity_in_stock: int
    estimated_delivery_days: Optional[int] = Field(
        default=None,
        description="ETA for replenishment when known."
    )


class DemandAnalysisResponse(BaseModel):
    """Structured response returned by the Demand Analyst."""

    status: Literal["available", "partial", "unavailable"]
    analysis_summary: str
    lacking_materials: List[LackingMaterial]


class ToolCall(BaseModel):
    """Decision emitted by the Demand Analyst router to select a tool."""

    tool_name: str = Field(description="Exact toolbox method name to call.")
    tool_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for the chosen tool."
    )
