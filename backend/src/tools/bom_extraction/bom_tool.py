from __future__ import annotations

import os
import cv2
import dspy

from backend.src.config import GEMINI_2_5_FLASH
from backend.src.models import BillOfMaterials
from backend.src.tools.bom_extraction.file_utils import fetch_file_via_ssh, convert_pdf_to_png
from backend.src.tools.bom_extraction.image_processing import (
    extract_bom_tight_crop,
    filter_unsafe_tables,
    merge_images_vertically
)



class BOMExtractionSignature(dspy.Signature):
    """Extract a structured BOM from the given technical drawing image."""

    drawing = dspy.InputField(desc="Customer technical drawing as an image.")
    bom: BillOfMaterials = dspy.OutputField(desc="Structured Bill of Materials extracted from the drawing.")


def _prepare_bom_image(file_path: str) -> str | None:
    """Normalize and crop the drawing into a single BOM image on disk.

    If ``file_path`` exists locally, it is used directly.
    Otherwise, we treat it as a remote identifier and fetch the file via SSH first.

    Returns the local image path to pass into the LLM, or None if no usable BOM tables were found.
    """
    # 1. Resolve the input into a local path (local path preferred, fallback to SSH)
    if os.path.exists(file_path):
        local_path = file_path
    else:
        local_path = fetch_file_via_ssh(file_path)

    local_path = convert_pdf_to_png(local_path)

    # 2. Normalize orientation (rotate if portrait)
    img_check = cv2.imread(local_path)
    if img_check is not None:
        h, w = img_check.shape[:2]
        if h > w:
            print(f"🔄 Detected vertical image ({w}x{h}). Rotating 90° right...")
            cv2.imwrite(local_path, cv2.rotate(img_check, cv2.ROTATE_90_CLOCKWISE))

    return local_path

def perform_bom_extraction(file_path: str) -> BillOfMaterials | str:
    """High-level BOM extraction tool used by the agent and tests.

    Args:
        file_path: Absolute/relative path to the drawing image, or an identifier
        that can be resolved on the remote system (for SSH-based lookup).

    Returns:
        A BillOfMaterials instance on success, or an error message string on
        failure. Callers should treat non-BillOfMaterials returns as failures.
    """
    print(f"🛠️ BOM extraction triggered for: {file_path}")
    try:
        merged_file_path = _prepare_bom_image(file_path)
        #if not merged_file_path:
            # No tables found – return an empty BOM rather than raising.
        #    return BillOfMaterials(items=[])

        #print(f"--- 🤖 Sending file path to Gemini: {merged_file_path} ---")
        dspy_image = dspy.Image(url=merged_file_path)

        # Use a BOM-optimised model while keeping the global default for other tools.
        with dspy.context(lm=GEMINI_2_5_FLASH):
            extractor = dspy.Predict(BOMExtractionSignature)
            prediction = extractor(drawing=dspy_image)

        return prediction.bom
    except Exception as exc:
        return f"Error extracting BOM: {exc}"
