"""BOM extraction tool exposed to the unified ReAct agent."""
import os
import dspy

from backend.src.config import GEMINI_2_5_FLASH
from backend.src.models import BillOfMaterials


class BOMExtraction(dspy.Signature):
    """Extract a structured BOM from the given technical drawing image."""
    drawing = dspy.InputField(desc="Customer technical drawing as an image.")
    bom: BillOfMaterials = dspy.OutputField(desc="Structured Bill of Materials.")


def perform_bom_extraction(file_path: str) -> BillOfMaterials | str:
    """
    Read an image file from disk and extract a structured Bill of Materials.

    Args:
        file_path: Absolute or relative path to the drawing image (e.g., 'uploads/drawing.png').

    Returns:
        BillOfMaterials on success; otherwise an error message string describing what failed
        (e.g., missing file, extraction error). The caller should treat non-BOM returns as failures.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    try:
        image = dspy.Image(file_path)

        with dspy.context(lm=GEMINI_2_5_FLASH):
            extractor = dspy.Predict(BOMExtraction)
            result = extractor(drawing=image)

        return result.bom
    except Exception as e:
        return f"Error extracting BOM: {str(e)}"


if __name__ == '__main__':
    bom = perform_bom_extraction('./example_bom.png')
    print(bom.model_dump_json(indent=2))
