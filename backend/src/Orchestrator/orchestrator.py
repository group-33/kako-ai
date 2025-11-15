# in orchestrator.py

import os
from typing import TypedDict, Optional, List, Dict, Literal
from pydantic import BaseModel, Field
from ..models import BillOfMaterials, BOMItem
from langgraph.graph import StateGraph, END


# --- 2. Define the Shared State ---
# We need to add new fields to our "central box" to handle the new steps

class KakoAIState(TypedDict):
    """
    The central state "box" for the new workflow.
    """
    # Inputs
    user_query: str                  # e.g., "Requests order situation"
    customer_drawing_file: str       # Path to the "Zeichnungen"
    
    # Data from Agents
    bom: Optional[BillOfMaterials]   # The BOM (either from DB or extractor)
    bom_exists_in_db: bool           # Flag from the first check
    demand_analysis_report: Optional[Dict] # From the Demand Analyst
    procurement_options: Optional[Dict]  # From the Procurement Agent
    
    # Fields for HITL and Loops
    user_feedback: Optional[str]     # User's feedback on procurement
    final_response: Optional[str]    # Final message for the user

# --- 3. Mock Agent Functions ---
# These are simple Python functions pretending to be your agents

def mock_check_bom_db(query: str) -> Dict:
    """MOCK: Pretends to be the Demand Analyst checking if a BOM exists."""
    print(f"[Mock Agent] Checking Xentral for existing BOM for '{query}'...")
    
    # Simulate "BOM is missing" to trigger extraction
    if "extract" in query.lower():
        print("[Mock Agent] --> BOM not found in Xentral.")
        return {"bom_exists_in_db": False, "bom": None}
    
    print("[Mock Agent] --> BOM found in Xentral.")
    mock_bom = BillOfMaterials(items=[BOMItem(part_number="PN-DB-123", quantity=1, description_of_part="BOM from DB")])
    return {"bom_exists_in_db": True, "bom": mock_bom}

def mock_bom_extractor(file_path: str) -> BillOfMaterials:
    """MOCK: Pretends to be your DSPY BOM Extractor."""
    print(f"[Mock Agent] Extracting BOM from {file_path}...")
    
    # --- THIS IS THE FIX ---
    # We now provide default values for all 6 required fields.
    mock_item = BOMItem(
        part_number="PN-EXT-456", 
        quantity=5, 
        description_of_part="Extracted Part",
        no_of_poles=0,
        order_number=9001,
        hdm_no=12345,
        measurments_in_discription="100x50mm"
    )
    
    return BillOfMaterials(items=[mock_item])

def mock_save_bom_to_xentral(bom: BillOfMaterials):
    """MOCK: Pretends to save the new BOM to the ERP."""
    print(f"[Mock Agent] Saving new BOM with {len(bom.items)} items to Xentral...")
    return {} # No state change needed

def mock_demand_analyst(bom: BillOfMaterials) -> Dict:
    """MOCK: Pretends to do the *real* inventory check (Step 7 in diagram)."""
    print(f"[Mock Agent] Running demand analysis (inventory check) for {len(bom.items)} items...")
    
    # Simulate "lacking materials" to trigger procurement
    print("[Mock Agent] --> Simulating LACKING materials.")
    return {
        "status": "partial",
        "lacking_materials": [{"part_number": "PN-EXT-456", "needed": 5, "in_stock": 2}]
    }

def mock_procurement_specialist(bom: BillOfMaterials, feedback: Optional[str] = None) -> Dict:
    """MOCK: Pretends to be the Octopart procurement specialist."""
    if feedback:
        print(f"[Mock Agent] Re-assessing procurement based on feedback: '{feedback}'")
        # New options based on feedback
        return {"options": "Option 2 (Cheaper, Slower)", "price": 40.0}
    else:
        print("[Mock Agent] Analyzing information and proposing order options...")
        # Initial options
        return {"options": "Option 1 (Fastest, Costly)", "price": 50.0}

def mock_confirm_procurement(options: Dict) -> str:
    """MOCK: Pretends to add the order to the Octopart shopping cart."""
    print(f"[Mock Agent] Adding '{options['options']}' to Octopart shopping cart...")
    return f"Order confirmed: {options['options']} for ${options['price']}"

# --- 4. Define the Agent Nodes (Stations) ---
# These are the "wrapper" functions that LangGraph calls.

def check_bom_db_node(state: KakoAIState):
    """Node 1: Checks if the BOM already exists in Xentral."""
    print("--- 🏭 Station: CHECK_BOM_DB ---")
    result = mock_check_bom_db(state["user_query"])
    return result

def bom_extractor_node(state: KakoAIState):
    """Node 2: Extracts BOM from customer document."""
    print("--- 🏭 Station: BOM_EXTRACTOR ---")
    bom = mock_bom_extractor(state["customer_drawing_file"])
    # This is where you would PAUSE for HITL 1
    return {"bom": bom}

def save_bom_to_xentral_node(state: KakoAIState):
    """Node 3: Saves the user-confirmed BOM to Xentral."""
    print("--- 🏭 Station: SAVE_BOM_TO_XENTRAL ---")
    mock_save_bom_to_xentral(state["bom"])
    return {} # No state change

def demand_analyst_node(state: KakoAIState):
    """Node 4: Runs the full inventory check (was 'feasibility_analyst')."""
    print("--- 🏭 Station: DEMAND_ANALYST ---")
    report = mock_demand_analyst(state["bom"])
    return {"demand_analysis_report": report}

def procurement_specialist_node(state: KakoAIState):
    """Node 5: Proposes procurement options or re-assesses based on feedback."""
    print("--- 🏭 Station: PROCUREMENT_SPECIALIST ---")
    options = mock_procurement_specialist(state["bom"], state.get("user_feedback"))
    # This is where you would PAUSE for HITL 2
    # Clear feedback after it's been used
    return {"procurement_options": options, "user_feedback": None}

def confirm_procurement_node(state: KakoAIState):
    """Node 6: Finalizes the order and sends to Octopart."""
    print("--- 🏭 Station: CONFIRM_PROCUREMENT ---")
    confirmation_msg = mock_confirm_procurement(state["procurement_options"])
    return {"final_response": confirmation_msg}

def generate_response_node(state: KakoAIState):
    """Node 7: Generates a simple 'all good' response if no procurement is needed."""
    print("--- 🏭 Station: GENERATE_RESPONSE ---")
    return {"final_response": "Demand analysis complete. All materials are in stock."}

# --- 5. Define the Conditional Logic (Routers) ---

def should_extract_bom(state: KakoAIState) -> Literal["extract_bom", "run_demand_analysis"]:
    """Router 1: Checks if BOM extraction is needed."""
    print("--- ⚖️  Router 1: should_extract_bom? ---")
    if state["bom_exists_in_db"]:
        print("--> Decision: BOM exists. Skipping extraction.")
        return "run_demand_analysis" # Skip to demand analysis
    else:
        print("--> Decision: BOM missing. Running extractor.")
        return "extract_bom"

def should_procure(state: KakoAIState) -> Literal["procure", "generate_response"]:
    """Router 2: Checks if procurement is needed."""
    print("--- ⚖️  Router 2: should_procure? ---")
    report = state["demand_analysis_report"]
    if report and report.get("lacking_materials"):
        print("--> Decision: Materials lacking. Routing to PROCUREMENT.")
        return "procure"
    else:
        print("--> Decision: All materials in stock. Routing to RESPONSE.")
        return "generate_response"

def handle_procurement_feedback(state: KakoAIState) -> Literal["feedback_loop", "confirm_order"]:
    """Router 3: Checks if the user provided feedback or confirmed."""
    print("--- ⚖️  Router 3: handle_procurement_feedback? ---")
    # In a real app, you'd get this from the user after the pause.
    # We will simulate it from the state.
    if state.get("user_feedback"):
        print("--> Decision: User gave feedback. Looping back.")
        return "feedback_loop"
    else:
        print("--> Decision: User confirmed. Finalizing order.")
        return "confirm_order"

# --- 6. Build the Orchestration Graph ---

print("\n--- 🏗️  Building KakoAI Graph (Diagram Version) ---")
workflow = StateGraph(KakoAIState)

# Add all the "stations" (nodes)
workflow.add_node("CHECK_BOM_DB", check_bom_db_node)
workflow.add_node("BOM_EXTRACTOR", bom_extractor_node)
workflow.add_node("SAVE_BOM_TO_XENTRAL", save_bom_to_xentral_node)
workflow.add_node("DEMAND_ANALYST", demand_analyst_node)
workflow.add_node("PROCUREMENT_SPECIALIST", procurement_specialist_node)
workflow.add_node("CONFIRM_PROCUREMENT", confirm_procurement_node)
workflow.add_node("GENERATE_RESPONSE", generate_response_node)

# --- Define the "assembly line" (edges) ---
workflow.set_entry_point("CHECK_BOM_DB")

# Router 1: After checking the DB, either extract or skip to analysis
workflow.add_conditional_edges(
    "CHECK_BOM_DB",
    should_extract_bom,
    {
        "extract_bom": "BOM_EXTRACTOR",
        "run_demand_analysis": "DEMAND_ANALYST"
    }
)

# This is the BOM extraction path
workflow.add_edge("BOM_EXTRACTOR", "SAVE_BOM_TO_XENTRAL")
workflow.add_edge("SAVE_BOM_TO_XENTRAL", "DEMAND_ANALYST")

# Router 2: After analysis, either procure or finish
workflow.add_conditional_edges(
    "DEMAND_ANALYST",
    should_procure,
    {
        "procure": "PROCUREMENT_SPECIALIST",
        "generate_response": "GENERATE_RESPONSE"
    }
)

# Router 3: The procurement loop!
workflow.add_conditional_edges(
    "PROCUREMENT_SPECIALIST",
    handle_procurement_feedback,
    {
        "feedback_loop": "PROCUREMENT_SPECIALIST", # <-- This creates the loop
        "confirm_order": "CONFIRM_PROCUREMENT"
    }
)

# Define the two final end points
workflow.add_edge("GENERATE_RESPONSE", END)
workflow.add_edge("CONFIRM_PROCUREMENT", END)

# Compile the graph
# (See section 7 for how to add real interrupts)
app = workflow.compile()
print("--- ✅ Graph Compiled Successfully ---")


# --- 7. How to Test This (Simulating the Interrupts) ---

if __name__ == "__main__":
    
    print("\n\n--- 🏁 TEST RUN: Full Loop (Extract > Procure > Feedback > Confirm) ---")
    
    # This input will trigger all nodes
    initial_input = {
        "user_query": "Test run with extract", # Triggers BOM extraction
        "customer_drawing_file": "path/to/drawing_B.pdf" 
    }
    
    # Use a 'thread' to maintain memory
    config = {"configurable": {"thread_id": "123"}}

    # 1. Run until the first pause (Procurement)
    # In a real app, we would add an interrupt after BOM_EXTRACTOR
    # For this test, we'll just simulate the whole flow.
    
    # Run until it hits the procurement specialist
    final_state = app.invoke(initial_input, config)

    # At this point, the graph has run, found lacking materials, and
    # proposed an option. The 'handle_procurement_feedback' router
    # saw 'user_feedback' was None, so it confirmed.
    
    print("\n--- ✅ Run 1 Complete (No Feedback) ---")
    print(f"Final Response: {final_state['final_response']}")


    print("\n\n--- 🏁 TEST RUN 2: Simulating the Feedback Loop ---")
    config = {"configurable": {"thread_id": "456"}}
    
    # We can 'inject' state to test the loop
    # We add 'user_feedback' to the *initial* call to simulate resuming
    # from a pause.
    input_with_feedback = {
        "user_query": "Test run with extract",
        "customer_drawing_file": "path/to/drawing_C.pdf",
        "user_feedback": "That's too expensive, find a cheaper option."
    }

    # Because 'user_feedback' is present, the procurement node will
    # "re-assess", and the router will loop back.
    # To test this properly, we need to add the real interrupts.
    
    # For now, this test shows the first run:
    final_state_2 = app.invoke(input_with_feedback, config)
    
    print("\n--- ✅ Run 2 Complete (With Feedback) ---")
    print(f"Final Response: {final_state_2['final_response']}")
    print("Note: The mock 'handle_procurement_feedback' router is set to 'confirm' by default.")
    print("To test the loop, you must use the real interrupt method.")