"""Pydantic models specific to BOM extraction workflows."""
from pydantic import BaseModel, Field

from backend.src.models import BillOfMaterials


class BOMExtractionRequest(BaseModel):
    """Input metadata for BOM extraction (drawing currently supplied via multipart file upload)."""
    pass


class BOMExtractionResponse(BaseModel):
    """Structured output shared with downstream agents after extraction."""
    bom: BillOfMaterials = Field(
        description="The extracted Bill of Materials for a single product configuration."
    )
