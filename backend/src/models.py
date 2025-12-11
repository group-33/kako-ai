"""Shared, cross-feature Pydantic models."""
from typing import List
from pydantic import BaseModel, Field


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
