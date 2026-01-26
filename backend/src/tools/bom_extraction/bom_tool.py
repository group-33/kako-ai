from __future__ import annotations

import os
import cv2
import dspy

from backend.src.models import BillOfMaterials
from backend.src.tools.bom_extraction.file_utils import fetch_file_via_ssh, convert_pdf_to_png
from backend.src.config import GEMINI_2_5_FLASH


class BOMExtractionSignature(dspy.Signature):
    """Extract a structured BOM from the given technical drawing image."""

    drawing = dspy.InputField(desc="Customer technical drawing as an image.")
    bom: BillOfMaterials = dspy.OutputField(desc="Structured Bill of Materials extracted from the drawing.")


def _resolve_local_path(file_path: str) -> str:
    """Return a local file path for the given drawing, fetching from SSH if needed."""
    # 1. Resolve the input into a local path (fallback to SSH fetch)
    local_path = file_path if os.path.exists(file_path) else fetch_file_via_ssh(file_path)
    return local_path


def _prepare_image_for_model(local_path: str) -> str:
    """Ensure the model gets an image. If PDF, convert first page to PNG."""
    if local_path.lower().endswith(".pdf"):
        # We create a separate png file for the model, but keep the original PDF for the UI
        return convert_pdf_to_png(local_path)
    
    # Normalize orientation if it's already an image
    img_check = cv2.imread(local_path)
    if img_check is not None:
        h, w = img_check.shape[:2]
        if h > w:
            cv2.imwrite(local_path, cv2.rotate(img_check, cv2.ROTATE_90_COUNTERCLOCKWISE))
    return local_path


def perform_bom_extraction(file_path: str) -> tuple[BillOfMaterials, str] | str:
    """High-level BOM extraction tool using remote/existing files.
    
    USE THIS TOOL WHEN:
    - The user refers to a known filename or path on the server (e.g. "order_123.pdf", "/volume1/...").
    - The file is NOT a new upload in this message.

    Args:
        file_path: Absolute/relative path to the drawing, or a remote search identifier.
    
    Returns:
        A tuple (BillOfMaterials, used_display_path) on success.
    """
    print(f"🛠️ BOM extraction triggered for: {file_path}")
    try:
        # 1. Get the actual file (PDF or Image)
        display_path = _resolve_local_path(file_path)
        
        # 2. Get an image version for the AI model
        model_image_path = _prepare_image_for_model(display_path)

        #print(f"--- 🤖 Sending file path to Gemini: {model_image_path} ---")
        dspy_image = dspy.Image(url=model_image_path)

        # Use a BOM-optimised model while keeping the global default for other tools.
        with dspy.context(lm=GEMINI_2_5_FLASH):
            extractor = dspy.Predict(BOMExtractionSignature)
            prediction = extractor(drawing=dspy_image)

        # Return the BOM AND the path to the ORIGINAL file for display (PDF or Image)
        return prediction.bom, display_path
    except Exception as exc:
        return f"Error extracting BOM: {exc}"

def perform_bom_extraction_upload(file: str) -> tuple[BillOfMaterials, str] | str:
    """High-level BOM extraction tool SPECIFICALLY for NEW USER UPLOADS.
    
    USE THIS TOOL ONLY WHEN:
    - The system prompt indicates "[SYSTEM: File uploaded at '...']".
    - The user says "extract from this file" referring to an attachment.
    
    Args:
        file: The absolute file path to the uploaded file provided by the system.

    Returns:
        A tuple (BillOfMaterials, used_display_path) on success, or an error message string on
        failure. Callers should treat non-tuple returns as failures.
    """
    try:
        if not os.path.exists(file):
            return f"Error: File not found at path '{file}'. Please ensure you are using the exact path provided by the system."

        display_path = file
        
        # Prepare image for model (separate file if converting)
        model_image_path = display_path
        if display_path.lower().endswith(".pdf"):
             print(f"📄 file is PDF, converting to PNG for AI model: {display_path}")
             model_image_path = convert_pdf_to_png(display_path)
        
        # If it's already an image (PNG, JPG, etc.), usage is direct.
        # We assume main.py has already saved it to a local temp path.

        print(f"--- 🤖 Sending file path to Gemini: {model_image_path} ---")
        # Ensure we use 'url' or 'path' depending on dspy version, usually url=path works for local files in some dspy versions
        # or dspy.Image(path)
        # Based on existing code: dspy.Image(url=...)
        dspy_image = dspy.Image(url=model_image_path)

        # Use a BOM-optimised model while keeping the global default for other tools.
        with dspy.context(lm=GEMINI_2_5_FLASH):
            extractor = dspy.Predict(BOMExtractionSignature)
            prediction = extractor(drawing=dspy_image)

        return prediction.bom, display_path
    except Exception as exc:
        return f"Error extracting BOM from upload: {exc}"
