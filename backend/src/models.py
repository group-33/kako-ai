"""Shared, cross-feature Pydantic models."""
from datetime import datetime
from typing import List, Literal, Union, Dict, Any, Optional

from pydantic import BaseModel, Field

"""
class BOMItem(BaseModel):
    part_number: str = Field(description="Position/part number as referenced in the drawing or ERP.")
    quantity: int = Field(description="Units of this component needed for one finished product.")
    description_of_part: str = Field(description="Human-readable label or description of the component.")
    no_of_poles: int = Field(description="Number of poles for the part (e.g., connector pins).")
    order_number: int = Field(description="Line or order position number from the source document.")
    hdm_no: int = Field(description="HDM identifier associated with the component.")
    measurements_in_description: str = Field(description="Dimension details captured from the drawing/description.")


class BillOfMaterials(BaseModel):
    items: List[BOMItem] = Field(description="All component line items that make up the BOM.")
"""
class BOMItem(BaseModel):
    part_number: int = Field(
        "1",
        description=(
            "The entry number of the item."
            "INSTRUCTION: If the drawing has explicit position numbers (e.g., 'Pos 10', '1.1'), extract them."
            "If the drawing has NO position numbers, you MUST generate them yourself sequentially (1, 2, 3...) " 
            "based on the order of the rows."
            )
        )
    quantity: Optional[float] = Field(
        None, 
        description=(
            "The numeric quantity required. Extract only the number. "
            "Example: if '1.5 m' is listed, extract 1.5."
        )
    )
    item_nr: Optional[str] = Field(
        None,
        description=(
            "The unique identifier, part number, or order code for the item."
        )
    )
    description: Optional[str] = Field(
        None, 
        description="The full human-readable description text of the component."
    )
    unit: str = Field(
        "pcs", 
        description=(
            "The unit of measurement (e.g., 'm', 'mm', 'kg', 'pcs'). "
            "If no unit is explicitly written, default to 'pcs'."
        )
    )

class BillOfMaterials(BaseModel):
    items: List[BOMItem] = Field(description="All component line items that make up the BOM.")
# --- API response models (backend -> frontend) --------------------------------


class TextBlock(BaseModel):
    """Standard text response block."""

    type: Literal["text"] = "text"
    content: str


class BOMRow(BaseModel):
    """Single row in a BOM table for frontend display."""

    id: str
    pos: str | int | None = None
    item_nr: str | None = None
    component: str  # Kept for backward compat (will map to description usually)
    description: str | None = None
    quantity: float
    unit: str
    confidence_score: float | None = None


class BOMTableData(BaseModel):
    """Payload for the BOM table tool."""

    rows: List[BOMRow]
    source_document: str | None = None


class ToolUseBlock(BaseModel):
    """Tool-use block that tells the frontend to render a specific component."""

    type: Literal["tool_use"] = "tool_use"
    tool_name: str
    data: Dict[str, Any]


ContentBlock = Union[TextBlock, ToolUseBlock]


class BOMOverride(BaseModel):
    """Editable overrides for a single BOM row (keyed by a stable item id)."""

    item_id: str
    quantity: float
    item_nr: str | None = None
    description: str | None = None
    unit: str | None = None
    component: str | None = None # Deprecated but kept for safety


class BOMUpdate(BaseModel):
    """Set of overrides to apply to the latest extracted BOM."""

    bom_id: str
    overrides: List[BOMOverride]


class AgentRequest(BaseModel):
    """Request payload for the unified agent endpoint."""

    user_query: str
    thread_id: str | None = None
    model_id: str | None = None
    bom_update: BOMUpdate | None = None


class AgentResponse(BaseModel):
    """Top-level response object returned by backend endpoints to the frontend."""

    response_id: str
    created_at: datetime
    blocks: List[ContentBlock]
