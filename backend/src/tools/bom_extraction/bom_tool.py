import dspy
from .dspy_modules import BOMExtractorModule

# Singleton Instance initialization
_extractor_instance = BOMExtractorModule()

class RetrieveBOM(dspy.Module):
    """
    A tool to extract the Bill of Materials (BOM) from a technical drawing.
    Input must be the filename of the drawing (e.g., "123-456.pdf").
    Returns a string representation of the parts list (JSON format).
    """
    name = "retrieve_bom"
    input_variable = "filename"
    desc = "Takes a filename of a technical drawing and returns the Bill of Materials (BOM) containing part numbers and quantities."

    def __call__(self, filename: str):
        print(f"\n[Tool] Agent requested BOM for: {filename}")
        try:
            bom_result = _extractor_instance.forward(filename)
            # Return JSON string for the Agent to read
            return bom_result.model_dump_json()
        except Exception as e:
            return f"Error: Failed to extract BOM. Reason: {str(e)}"