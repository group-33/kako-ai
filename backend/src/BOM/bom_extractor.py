# bom_extractor.py
import dspy
from pydantic import BaseModel, Field
from typing import List
from ..models import  BillOfMaterials
# 1. Define the Pydantic models for our structured output
# This defines a single item in the BOM


# This defines the full Bill of Materials, which is a list of the items above


# 2. Define the DSPy Signature
class BOMExtractionSignature(dspy.Signature):
    """
    Extracts all components, part numbers, and quantities from a technical drawing.
    Outputs the result as a structured Bill of Materials (BOM).
    """
    
    # Input: We'll pass the drawing (as an image) to this field.
    drawing = dspy.InputField(desc="The customer's technical drawing ('Zeichnung').")
    
    # Output: We tell DSPy the output *must* follow the BillOfMaterials Pydantic model.
    bom: BillOfMaterials = dspy.OutputField()
# bom_extractor.py (continued...)

# 3. Define the DSPy Module (the agent)
class BOMExtractor(dspy.Module):
    def __init__(self):
        super().__init__()
        # We use ChainOfThought to force the LM to "think" before answering,
        # which improves accuracy for complex tasks like this.
        self.extractor = dspy.ChainOfThought(BOMExtractionSignature)

    def forward(self, drawing_image):
        # The 'drawing' input in our signature will be filled by 'drawing_image'
        result = self.extractor(drawing=drawing_image)
        return result
# bom_extractor.py (continued...)

def test_bom_extractor():
    print("--- 1. Configuring LM ---")
    YOUR_API_KEY = ""
    
    # We use a vision-capable model.
    # gemini/gemini-2.5-flash is fast and free.
    lm = dspy.LM(model='gemini/gemini-2.5-flash', api_key=YOUR_API_KEY)
    dspy.settings.configure(lm=lm)
    
    # --- 2. Load Your Drawing ---
    # !! REPLACE THIS with the path to your test image !!
    YOUR_DRAWING_PATH = "/home/jason-mann/Desktop/GenAI_projekt/Screenshot from 2025-11-04 12-48-04.png" 
    
    try:
        # dspy.Image handles loading the image from the file path
        drawing_image = dspy.Image(url=YOUR_DRAWING_PATH)
        print(f"--- 2. Loaded Drawing: {YOUR_DRAWING_PATH} ---")
    except Exception as e:
        print(f"ERROR: Could not load image. Make sure the path is correct.")
        print(f"Details: {e}")
        return

    # --- 3. Initialize and Run the Agent ---
    print("--- 3. Initializing BOMExtractor Agent ---")
    bom_agent = BOMExtractor()
    
    print("--- 4. Running Extraction (this may take a moment)... ---")
    try:
        # This is where the magic happens!
        result = bom_agent(drawing_image=drawing_image)
        
        print("\n--- 5. EXTRACTION COMPLETE ---")
        print("Raw Output (Pydantic Model):")
        print(result.bom)
        
        print("\nPretty JSON Output:")
        # .model_dump_json() is a Pydantic function to get clean JSON
        print(result.bom.model_dump_json(indent=2))
        
    except Exception as e:
        print("\n--- EXTRACTION FAILED ---")
        print(f"An error occurred: {e}")
        print("\n--- DEBUG: Last LM Request/Response ---")
        # This is super useful for debugging!
        lm.inspect_history(n=1)


# This makes the script runnable
if __name__ == "__main__":
    test_bom_extractor()