"""Pydantic models that define the agent IO contracts."""
from pydantic import BaseModel, Field
from typing import List


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
