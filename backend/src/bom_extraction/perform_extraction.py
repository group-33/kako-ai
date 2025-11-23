from __future__ import annotations

import dspy

from backend.src.models import BillOfMaterials
from backend.src.config import GOOGLE_API_KEY

dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash", api_key=GOOGLE_API_KEY))


class BOMExtraction(dspy.Signature):
    """Extract a structured BOM from a technical drawing ('Zeichnung')."""

    drawing = dspy.InputField(desc="Customer technical drawing as an image.")
    bom: BillOfMaterials = dspy.OutputField(desc="Structured Bill of Materials.")


def run_bom_extraction(drawing_image: dspy.Image) -> BillOfMaterials:
    """
    Run BOM extraction on a given image and return the BillOfMaterials.

    Configure your LM with a vision-capable model (e.g., gemini) before calling.
    """
    bom_extractor = dspy.Predict(BOMExtraction)
    result = bom_extractor(drawing=drawing_image)
    return result.bom


if __name__ == "__main__":
    image = dspy.Image('./example_bom.png')
    bom = run_bom_extraction(image)
    print(bom.model_dump_json(indent=2))
