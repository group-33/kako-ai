import dspy
from .dspy_modules import BOMExtractorModule
import dspy
# Assume BOMExtractor is defined or imported above...
from backend.src.models import BillOfMaterials

# 1. Initialize the Engine (Singleton)
_engine = BOMExtractorModule()

# =========================================================
# LAYER 1: The Service (Clean Python Interface)
# =========================================================
def perform_bom_extraction(filename: str) -> BillOfMaterials | str:
    """
    The core logic function. Returns a Pydantic object or Error string.
    Great for unit tests or using in other parts of your app.
    """
    print(f"🛠️ Service Triggered: {filename}")
    try:
        # Call the heavy lifter
        result = _engine.forward(filename)
        return result
    except Exception as e:
        return f"Error extracting BOM: {str(e)}"

# =========================================================
# LAYER 2: The DSPy Tool (Agent Interface)
# =========================================================
class RetrieveBOM(dspy.Module):
    """
    The wrapper that makes the Service usable by the AI Agent.
    Handles JSON conversion and Tool Description.
    """
    # Metadata the Agent reads to understand the tool
    name = "retrieve_bom"
    input_variable = "filename"
    desc = "Takes a filename of a technical drawing and returns the Bill of Materials (BOM) containing part numbers and quantities."

    def __call__(self, filename: str):
        print(f"\n[Tool] Agent called RetrieveBOM for: {filename}")
        
        # 1. Call Layer 1
        result = perform_bom_extraction(filename)
        
        # 2. Handle the output format for the LLM
        if isinstance(result, str):
            # It was an error message
            return result
        
        # 3. Convert Object -> JSON String (LLMs read text, not Objects)
        return result.model_dump_json()