import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from backend.src.tools.demand_analysis.bom import check_feasibility
from backend.src.models import BillOfMaterials, BOMItem

def run_showcase():
    print("--- Feasibility Check Showcase (Real Data) ---")
    
    # Product ID 3 (part number 9142083116) has Stock 81, Min 20.
    item = BOMItem(
        position=1,
        quantity=1.0,
        description="Showcase Part",
        item_nr="9142083116", # Resolves to Xentral ID 3
        part_number="9142083116"
    )
    
    bom = BillOfMaterials(
        project_id="ShowcaseProject",
        items=[item]
    )
    
    print(f"Created BOM Model with item: {item.item_nr}")
    
    scenarios = [
        (50, "Safe Order"),      # Req 50, Rem 31 (>20) -> OK
        (65, "Warning Zone"),    # Req 65, Rem 16 (<20) -> Warning
        (90, "Infeasible")       # Req 90, Rem -9 -> Fail
    ]
    
    for amount, label in scenarios:
        print(f"\nTesting {label} (Amount: {amount})...")
        try:
            result_json = check_feasibility(bom, order_amount=amount)
            result = json.loads(result_json)
            
            print(f"Feasible: {result['feasible']}")
            if result['warnings']:
                print("Warnings:")
                for w in result['warnings']:
                    print(f"  - {w['message']}")
            
            if result['missing_items']:
                print("Missing Items:")
                for m in result['missing_items']:
                    print(f"  - {m['name']}: In Stock {m['in_stock']}, Needed {m['total_required']}")
                    
        except Exception as e:
            print(f"Error checking feasibility: {e}")

if __name__ == "__main__":
    run_showcase()
