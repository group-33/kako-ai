from __future__ import annotations

import os
import cv2
import dspy

from backend.src.models import BillOfMaterials
from backend.src.tools.bom_extraction.file_utils import fetch_file_via_ssh, convert_pdf_to_png


class BOMExtractionSignature(dspy.Signature):
    """Extract a structured BOM from the given technical drawing image."""

    drawing = dspy.InputField(desc="Customer technical drawing as an image.")
    bom: BillOfMaterials = dspy.OutputField(desc="Structured Bill of Materials extracted from the drawing.")


def _prepare_bom_image(file_path: str) -> str:
    """Return a local image path for the given drawing."""
    # 1. Resolve the input into a local path (fallback to SSH fetch)
    local_path = file_path if os.path.exists(file_path) else fetch_file_via_ssh(file_path)
    local_path = convert_pdf_to_png(local_path)

    # 2. Normalize orientation (rotate if portrait)
    img_check = cv2.imread(local_path)
    if img_check is not None:
        h, w = img_check.shape[:2]
        if h > w:
            cv2.imwrite(local_path, cv2.rotate(img_check, cv2.ROTATE_90_COUNTERCLOCKWISE))

    return local_path


def perform_bom_extraction(file_path: str) -> BillOfMaterials | str:
    """Extract a BOM from a local path or a remote filename."""
    try:
        image_path = _prepare_bom_image(file_path)
        dspy_image = dspy.Image(url=image_path)
        extractor = dspy.Predict(BOMExtractionSignature)
        prediction = extractor(drawing=dspy_image)
        return prediction.bom
    except Exception as exc:
        return f"Error extracting BOM: {exc}"
