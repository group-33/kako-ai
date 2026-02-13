from __future__ import annotations

import os
import hashlib
import cv2
import dspy

from backend.src.models import RawBillOfMaterials, BillOfMaterials, BOMItem
from backend.src.tools.bom_extraction.file_utils import (
    fetch_file_via_ssh,
    convert_pdf_to_png,
    get_pdf_orientation,
)
from backend.src.tools.demand_analysis.bom import perform_bom_matching
from backend.src.auth_context import is_current_user_mock
from backend.src.tools.bom_extraction.bom_cache import BOMCache
from backend.src.config import BOM_CACHE_ENABLED, BOM_CACHE_PATH


class BOMExtractionSignature(dspy.Signature):
    """Extract a structured BOM from the given technical drawing image.

    Ensure you extract the table rows accurately.
    """

    drawing = dspy.InputField(desc="Customer technical drawing as an image.")
    bom: RawBillOfMaterials = dspy.OutputField(
        desc="Structured Bill of Materials extracted from the drawing."
    )


def _bom_cache_prefix() -> str:
    settings = getattr(dspy, "settings", None)
    lm = getattr(settings, "lm", None) if settings else None
    model_id = getattr(lm, "model", None) or ""
    prompt = "\n".join(
        s
        for s in [
            (BOMExtractionSignature.__doc__ or "").strip(),
            getattr(getattr(BOMExtractionSignature, "drawing", None), "desc", "") or "",
            getattr(getattr(BOMExtractionSignature, "bom", None), "desc", "") or "",
        ]
        if s
    ).strip()
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest() if prompt else ""
    if model_id and prompt_hash:
        return f"{model_id}:{prompt_hash}"
    return model_id or prompt_hash


CACHE = BOMCache(
    path=BOM_CACHE_PATH,
    enabled=BOM_CACHE_ENABLED,
    key_prefix=_bom_cache_prefix(),
)


def _resolve_local_path(file_path: str) -> tuple[str, str, bool]:
    """Return a local file path for the given drawing, fetching from SSH if needed.

    Returns:
        (local_path, resolved_filename, is_exact_match)
    """
    # 1. Resolve the input into a local path (User upload or local dev)
    if os.path.exists(file_path):
        return file_path, os.path.basename(file_path), True

    # Check Mock User Restriction
    if is_current_user_mock():
        raise PermissionError(f"I cannot search the server for '{os.path.basename(file_path)}' in Mock Mode. Please upload the file manually.")

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


def perform_bom_extraction(file_path: str) -> str | tuple[BillOfMaterials, str]:
    """Extract a BOM from a local path or a remote filename."""
    try:
        # 1. Get the actual file (PDF or Image) - works for both local uploads and remote lookups
        display_path, resolved_filename, is_exact_match = _resolve_local_path(file_path)
        if not is_exact_match:
            return f"Did not find drawing '{file_path}'. Did you mean '{resolved_filename}'?"

        # 2. Get an image version for the AI model
        model_image_path = _prepare_image_for_model(display_path)

        # Check if we already ran extraction for this image, if so skip it
        full_bom = CACHE.get_full_bom(model_image_path)
        if full_bom is None:
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

            full_bom = BillOfMaterials(
                items=full_items, 
                title=raw_bom.title,
                orientation=get_pdf_orientation(display_path)
            )

            # Persist the full (pre-enrichment) BOM so future runs can skip the LLM
            CACHE.set_full_bom(model_image_path, full_bom)

        # 4. Enrich Data (Database Step)
        enriched_bom = perform_bom_matching(full_bom)
        
        # 5. Save to BOM Store (Context)
        import uuid
        from backend.src.store import BOMStore
        
        bom_id = f"BOM_{uuid.uuid4().hex[:8].upper()}"
        store = BOMStore()
        store.save_bom(bom_id, enriched_bom, source_document=resolved_filename)

        title = enriched_bom.title or 'Untitled'
        summary = (
            f"USER_VIEW: BOM '{title}' extracted successfully.\n"
            f"AGENT_DATA: Reference ID: {bom_id}, Source: {resolved_filename}, "
            f"Title: {title}, Content: {str(enriched_bom)}"
        )
        print(f"--- [BOM Extraction] Saved as {bom_id} ---")

        return summary
    except PermissionError as e:
        return f"{e}"
    except Exception as exc:
        return f"Error extracting BOM: {exc}"
