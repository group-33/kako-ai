from __future__ import annotations

import os
import cv2
import dspy

from backend.src.models import RawBillOfMaterials, BillOfMaterials, BOMItem
from backend.src.tools.bom_extraction.file_utils import (
    fetch_file_via_ssh,
    convert_pdf_to_png,
)
from backend.src.tools.demand_analysis.bom import perform_bom_matching
from backend.src.tools.bom_extraction.bom_cache import BOMCache
from backend.src.config import BOM_CACHE_ENABLED, BOM_CACHE_PATH


CACHE = BOMCache(path=BOM_CACHE_PATH, enabled=BOM_CACHE_ENABLED)


class BOMExtractionSignature(dspy.Signature):
    """Extract a structured BOM from the given technical drawing image.

    Ensure you extract the table rows accurately.
    Also extract the drawing title from the title block if present.
    """

    drawing = dspy.InputField(desc="Customer technical drawing as an image.")
    bom: RawBillOfMaterials = dspy.OutputField(
        desc="Structured Bill of Materials extracted from the drawing."
    )


def _resolve_local_path(file_path: str) -> tuple[str, str, bool]:
    """Return a local file path for the given drawing, fetching from SSH if needed.

    Returns:
        (local_path, resolved_filename, is_exact_match)
    """
    # 1. Resolve the input into a local path (User upload or local dev)
    if os.path.exists(file_path):
        return file_path, os.path.basename(file_path), True

    # 2. Fallback to SSH fetch if it's a remote file reference
    return fetch_file_via_ssh(file_path)


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
            cv2.imwrite(
                local_path, cv2.rotate(img_check, cv2.ROTATE_90_COUNTERCLOCKWISE)
            )
    return local_path


def perform_bom_extraction(file_path: str) -> tuple[RawBillOfMaterials, str] | str:
    """Extract a BOM from a local path or a remote filename."""
    try:
        # 1. Get the actual file (PDF or Image) - works for both local uploads and remote lookups
        display_path, resolved_filename, is_exact_match = _resolve_local_path(file_path)

        # If the user asked for a file but we found a fuzzy match remotely, stop and ask.
        # Compare file_path (input) with resolved_filename.
        # Note: If input was "/tmp/foo.pdf" (upload), is_exact_match is True.
        # If input was "Drawing123" and we found "Drawing123_v2.pdf", is_exact_match is False.
        if not is_exact_match:
            return f"Did not find drawing '{file_path}'. Did you mean '{resolved_filename}'?"

        # 2. Get an image version for the AI model
        model_image_path = _prepare_image_for_model(display_path)

        # Check if we already ran extraction for this image, if so skip it
        if CACHE.is_in_cache(model_image_path):
            full_bom = CACHE.get_full_bom(model_image_path)
        else:
            # 3. Perform the actual extraction
            dspy_image = dspy.Image(url=model_image_path)
            extractor = dspy.Predict(BOMExtractionSignature)
            prediction = extractor(drawing=dspy_image)

            # Return the BOM AND the path to the ORIGINAL file for display (PDF or Image)
            raw_bom = prediction.bom
            full_items = []
            for raw_item in raw_bom.items:
                # Create a BOMItem using the data extracted by the AI
                full_item = BOMItem(**raw_item.dict())
                full_items.append(full_item)

            full_bom = BillOfMaterials(items=full_items, title=raw_bom.title)

            # Persist the full (pre-enrichment) BOM so future runs can skip the LLM
            CACHE.set_full_bom(model_image_path, full_bom)

        # 4. Enrich Data (Database Step)
        # Now we look up the Xentral IDs using the clean extracted data
        enriched_bom = perform_bom_matching(full_bom)
        print(enriched_bom)

        return enriched_bom, display_path
    except Exception as exc:
        return f"Error extracting BOM: {exc}"
