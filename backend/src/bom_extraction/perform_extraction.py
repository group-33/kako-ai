from __future__ import annotations

import dspy

from backend.src.models import BillOfMaterials
from backend.src.config import GEMINI_2_5_FLASH


class BOMExtraction(dspy.Signature):
    """Extract a structured BOM from a technical drawing ('Zeichnung')."""
    drawing = dspy.InputField(desc="Customer technical drawing as an image.")
    bom: BillOfMaterials = dspy.OutputField(desc="Structured Bill of Materials.")


def run_bom_extraction(
    drawing_image: dspy.Image,
    extractor: dspy.Module | None = None
) -> BillOfMaterials:
    """
    Run BOM extraction on a given image and return the BillOfMaterials.

    Args:
        drawing_image: The DSPy image object.
        extractor: Optional pre-instantiated DSPy module (dependency injection).
                   If None, a fresh predictor is created (useful for local scripts).
    """
    if extractor is None:
        extractor = dspy.Predict(BOMExtraction)

    result = extractor(drawing=drawing_image)
    return result.bom


if __name__ == "__main__":
    with dspy.context(lm=GEMINI_2_5_FLASH):
        image = dspy.Image('./example_bom.png')
        bom = run_bom_extraction(image)
        print(bom.model_dump_json(indent=2))
