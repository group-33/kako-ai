"""Pydantic models specific to BOM extraction workflows."""
from typing import Optional

from pydantic import BaseModel, Field

from backend.src.models import BillOfMaterials


class BOMExtractionRequest(BaseModel):
    """Input metadata for BOM extraction (file, path, or URL)."""
    image_path: Optional[str] = Field(
        default=None,
        description="Local filesystem path to the drawing to extract the BOM from."
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Publicly reachable URL to the drawing to extract the BOM from."
    )


class BOMExtractionResponse(BaseModel):
    """Structured output shared with downstream agents after extraction."""
    bom: BillOfMaterials = Field(
        description="The extracted Bill of Materials for a single product configuration."
    )
