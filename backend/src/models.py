"""Pydantic models that define the agent IO contracts."""
from pydantic import BaseModel, Field
from typing import List


class BOMItem(BaseModel):
    """Represents a single component in a BOM."""

    # TODO
    # part_number: str = Field(..., description="Manufacturer or internal part number")

class BOMExtractionRequest(BaseModel):
    """Input expected by the BOM extractor agent."""

    # TODO


class BOMExtractionResponse(BaseModel):
    """Response shared with downstream agents."""

    # TODO
    # order_id: str
    # items: List[BOMItem]
