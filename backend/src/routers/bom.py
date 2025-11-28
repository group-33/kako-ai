"""Endpoints for BOM-related workflows."""
import dspy
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.src.bom_extraction.perform_extraction import run_bom_extraction
from backend.src.bom_extraction.models import BOMExtractionResponse

router = APIRouter(prefix="/bom", tags=["bom"])


def get_bom_extractor(request: Request) -> dspy.Module:
    extractor = getattr(request.app.state, "bom_extractor", None)
    if extractor is None:
        raise RuntimeError("BOM extractor not initialized.")
    return extractor


@router.post("/extract", response_model=BOMExtractionResponse)
async def extract_bom(
    extractor: dspy.Module = Depends(get_bom_extractor),
    file: UploadFile = File(...),
) -> BOMExtractionResponse:
    """Extract a structured BOM from an uploaded drawing."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    drawing_image = dspy.Image(content)

    try:
        bom = run_bom_extraction(drawing_image, extractor=extractor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    return BOMExtractionResponse(bom=bom)
