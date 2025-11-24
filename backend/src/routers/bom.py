"""Endpoints for BOM-related workflows."""
import dspy
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from backend.src.bom_extraction.models import BOMExtractionResponse
from backend.src.models import BillOfMaterials

router = APIRouter(prefix="/bom", tags=["bom"])


def get_bom_extractor(request: Request) -> dspy.Module:
    extractor = getattr(request.app.state, "bom_extractor", None)
    if extractor is None:
        raise RuntimeError("BOM extractor not initialized.")
    return extractor


@router.post("/extract", response_model=BOMExtractionResponse)
async def extract_bom(
    extractor: dspy.Module = Depends(get_bom_extractor),
    file: UploadFile | None = File(None),
    image_path: str | None = Form(None),
    image_url: str | None = Form(None),
) -> BOMExtractionResponse:
    """Extract a structured BOM from an uploaded drawing or a provided path/URL."""
    if file is not None:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        drawing_image = dspy.Image(content)
    else:
        image_source = image_path or image_url
        if not image_source:
            raise HTTPException(status_code=400, detail="Provide image_path or image_url when no file is uploaded.")
        drawing_image = dspy.Image(image_source)

    result = extractor(drawing=drawing_image)

    if not isinstance(result.bom, BillOfMaterials):
        raise HTTPException(status_code=500, detail="Extraction did not return a BOM.")

    return BOMExtractionResponse(bom=result.bom)
