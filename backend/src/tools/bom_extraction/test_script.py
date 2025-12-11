import sys
import os
import dspy
from dotenv import load_dotenv

# 1. Setup paths so Python finds your backend code
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../.."))
sys.path.append(project_root)

# 2. Load Environment Variables
load_dotenv(os.path.join(project_root, ".env"))

# 3. Import BOTH the Tool Class and the Function
from backend.src.tools.bom_extraction.bom_tool import RetrieveBOM, perform_bom_extraction
from backend.src.models import BillOfMaterials

# --- CONFIGURATION ---
TEST_FILENAME = "4000019-1210.00." 
# ---------------------

def run_test():
    print(f"--- ⚙️ Configuring Gemini ---")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    # Initialize the model
    lm = dspy.LM(model='gemini/gemini-2.5-flash', api_key=api_key)
    dspy.settings.configure(lm=lm)
    
    print(f"--- 🧪 Testing BOM Extraction with file: {TEST_FILENAME} ---")

    # ==========================================
    # TEST 1: The Service Layer (perform_bom_extraction)
    # ==========================================
    print("\n[Test 1/2] Testing 'perform_bom_extraction' (Python Object)...")
    try:
        # This should return a Pydantic Model (BillOfMaterials)
        result_obj = perform_bom_extraction(TEST_FILENAME)
        
        if isinstance(result_obj, BillOfMaterials):
            print(f"   ✅ Success! Returned valid Pydantic Object with {len(result_obj.items)} items.")
            # Optional: Print first item to verify data
            if result_obj.items:
                print(f"   Example Item: {result_obj.items[0]}")
        else:
            print(f"   ❌ Failed. Expected BillOfMaterials, got: {type(result_obj)}")
            print(f"   Response: {result_obj}")

    except Exception as e:
        print(f"   ❌ Exception in Service Layer: {e}")

    # ==========================================
    # TEST 2: The Agent Tool Layer (RetrieveBOM)
    # ==========================================
    print("\n[Test 2/2] Testing 'RetrieveBOM' Tool (Agent JSON String)...")
    
    # Initialize the tool
    bom_tool = RetrieveBOM()
    
    try:
        # Run the tool (should return a JSON string)
        result_json = bom_tool(TEST_FILENAME)
        
        # Verify it is a string (what the LLM expects)
        if isinstance(result_json, str) and "{" in result_json:
            print("   ✅ Success! Returned valid JSON String.")
            print("\n--- 📄 FINAL OUTPUT (Snippet) ---")
            print(result_json[:500] + "...") # Print first 500 chars to avoid spam
        else:
            print(f"   ❌ Failed. Expected JSON String, got: {type(result_json)}")
            
    except Exception as e:
        print(f"   ❌ Exception in Tool Layer: {e}")

if __name__ == "__main__":
    run_test()