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

# 3. Import the Tool
from backend.src.tools.bom_extraction.bom_tool import RetrieveBOM

# --- CONFIGURATION ---
TEST_FILENAME = "4000019-1210.00." 
# ---------------------

def run_test():
    print(f"--- ⚙️ Configuring Gemini ---")
    
    # CRITICAL FIX: Configure DSPy with the LM before running the tool
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    # Initialize the model
    lm = dspy.LM(model='gemini/gemini-2.5-flash', api_key=api_key)
    dspy.settings.configure(lm=lm)
    
    print(f"--- 🧪 Testing BOM Tool with file: {TEST_FILENAME} ---")
    
    # Initialize the tool
    bom_tool = RetrieveBOM()
    
    try:
        # Run the tool (returns a JSON string)
        result_json = bom_tool(TEST_FILENAME)
        
        print("\n--- ✅ OUTPUT (BOM) ---")
        print(result_json)
        
    except Exception as e:
        print(f"\n--- ❌ FAILED ---")
        print(e)
        # Optional: Inspect what happened if it failed during the LLM call
        # lm.inspect_history(n=1)

if __name__ == "__main__":
    run_test()