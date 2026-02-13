
"""
Mock data provider for the 'demand_analysis' tools.
Used when the user context indicates a restricted/mock environment (e.g. Professor).
"""
import random
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
from backend.src.models import BillOfMaterials, BOMItem

# --- Helpers ---

def _hash_str_to_int(s: str) -> int:
    """Deterministic hash of a string to an integer."""
    return int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16)

def _generate_mock_part_status(part_number: str, name: str, qty_required: float, sku: str = None) -> Dict[str, Any]:
    """
    Generate a deterministic stock status.
    Prioritizes SKU > Name > Part Number for seeding.
    """
    # 1. Determine Seed Key
    if sku and sku != "NOT_FOUND" and sku != "UNKNOWN":
        seed_key = sku
    elif name and name != "Unknown" and name != "Product from ID":
        seed_key = name
    else:
        seed_key = str(part_number)

    # Delegate to shared stock generator
    stock_data = _get_deterministic_stock(seed_key)
    
    stock = stock_data["stock"]
    min_stock = stock_data["min_stock"]

    # Calculate Feasibility and Warnings
    is_enough = stock >= qty_required
    warning_msg = None
    
    remaining = stock - qty_required
    if is_enough and remaining < min_stock:
        warning_msg = f"Stock will fall below minimum! (Remaining: {remaining:.1f}, Min: {min_stock}) [MOCK]"
    
    return {
        "part_number": sku if sku else part_number, # Return SKU if we have it, else Pos
        "name": name,
        "required_per_unit": qty_required,
        "total_required": qty_required, 
        "in_stock": stock,
        "min_stock": min_stock,
        "feasible": is_enough,
        "warning": warning_msg
    }

def _get_deterministic_stock(key: str) -> Dict[str, int]:
    """Shared logic to get stock from a key (SKU/ID/Name)."""
    seed_val = _hash_str_to_int(str(key))
    random.seed(seed_val)
    
    scenario_roll = random.random()
    
    if scenario_roll < 0.7:
        stock = random.randint(50, 500)
        min_stock = random.randint(1, 10)
    elif scenario_roll < 0.9:
        min_stock = random.randint(10, 50)
        stock = random.randint(min_stock, min_stock + 20) 
    else:
        stock = random.randint(0, 5)
        min_stock = random.randint(5, 20)
        
    return {"stock": stock, "min_stock": min_stock}

# --- Tools ---

def get_mock_inventory(product_id: str) -> dict:
    """Return a deterministic but realistic mock inventory status."""
    # Use shared logic
    stock_data = _get_deterministic_stock(product_id)
    
    return {
        "stock": stock_data["stock"],
        "min_stock": stock_data["min_stock"],
        "source": "MOCK_DATA"
    }

def get_mock_sales_orders(time_quantity: str, time_unit: str) -> list:
    """Return a rich list of mock sales orders to demonstrate timeline parsing."""
    return [
        {
            "id": "MOCK-ORD-101",
            "belegnr": "AT-2024-MOCK-A",
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "tatsaechlichesLieferdatum": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "status": "versendet",
            "kundennummer": "CUST-BMW-MOCK",
            "positionen": [
                {"id": "mock1", "artikel": "8001", "nummer": "CTRL-UNIT-X7", "bezeichnung": "Control Unit X7 (Mock)", "menge": 100},
                {"id": "mock2", "artikel": "8002", "nummer": "SENSOR-PRO", "bezeichnung": "Proximity Sensor", "menge": 500}
            ]
        },
        {
            "id": "MOCK-ORD-102",
            "belegnr": "AT-2024-MOCK-B",
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "tatsaechlichesLieferdatum": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "status": "in_produktion",
            "kundennummer": "CUST-SIEMENS-MOCK",
            "positionen": [
                {"id": "mock3", "artikel": "8003", "nummer": "HOUSING-ALU", "bezeichnung": "Aluminum Housing Type B", "menge": 50}
            ]
        },
        {
            "id": "MOCK-ORD-103",
            "belegnr": "AT-2024-MOCK-C",
            "datum": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "tatsaechlichesLieferdatum": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "status": "angelegt",
            "kundennummer": "CUST-BOSCH-MOCK",
            "positionen": [
                 {"id": "mock4", "artikel": "8004", "nummer": "CONN-M12", "bezeichnung": "M12 Connector (5-pole)", "menge": 2000}
            ]
        }
    ]

def get_mock_future_boms(time_quantity: str, time_unit: str) -> dict:
    """Return mock aggregated BOMs for orders, dynamically generated based on time window."""
    # Seed based on time window to give consistent results for same query
    seed_val = _hash_str_to_int(f"{time_quantity}-{time_unit}")
    random.seed(seed_val)
    
    # Generate 3-5 mock product BOMs
    count = random.randint(3, 5)
    details = []
    
    for i in range(count):
        pid = f"800{i}"
        details.append({
            "parent_product_id": pid,
            "parent_product_name": f"Mock Product {chr(65+i)} (Generated)",
            "bom_components": [
                 {"part_id": f"900{i}1", "nummer": f"PCB-V{i}", "name": f"PCB Board Rev {i}", "amount": 1},
                 {"part_id": f"900{i}2", "nummer": f"MCU-{i}00", "name": f"Microcontroller Type {i}", "amount": 1},
                 {"part_id": f"900{i}3", "nummer": "STD-RES", "name": "Standard Resistor", "amount": random.randint(5, 20)}
            ]
        })

    return {
        "summary": f"Found {count} products with BOMs for orders in the next {time_quantity} {time_unit} (MOCK)",
        "details": details
    }

def get_mock_orders_by_customer(customer_id: str) -> list:
    """Return mock orders for a specific customer."""
    # Deterministic list based on customer_id length/hash to vary it slightly
    # Use hash for more variance than length
    seed_val = _hash_str_to_int(customer_id)
    random.seed(seed_val)
    
    count = random.randint(2, 5)
    orders = []
    
    for i in range(count):
        ord_num = random.randint(1000, 9999)
        orders.append({
            "id": f"MOCK-ORD-{customer_id}-{ord_num}",
            "belegnr": f"AT-2024-{customer_id}-{ord_num}",
            "datum": "2024-02-01",
            "tatsaechlichesLieferdatum": "2024-02-28",
            "status": "offen",
            "kundennummer": customer_id,
            "positionen": [
                {"id": f"pos{i}", "artikel": "9999", "nummer": "CUSTOM-PART-Z", "bezeichnung": f"Custom Part for {customer_id}", "menge": (i+1)*5}
            ]
        })
    return orders

def get_mock_boms_for_orders(order_numbers: list) -> dict:
    results = {}
    for order_nr in order_numbers:
        # Generate specific mocks for this order number
        seed_val = _hash_str_to_int(str(order_nr))
        random.seed(seed_val)
        
        num_products = random.randint(1, 3)
        found_boms = []
        
        for i in range(num_products):
             found_boms.append({
                "product_number": f"MOCK-PROD-{order_nr}-{i}",
                "product_id": f"888{i}",
                "bom": [
                    {"part_id": f"777{i}", "nummer": f"SUB-COMP-{i}", "name": f"Subcomponent {chr(65+i)}", "amount": random.randint(1, 10)},
                    {"part_id": f"888{i}", "nummer": "SCREW-M4", "name": "Screw M4x10", "amount": random.randint(4, 12)}
                ]
            })
            
        results[order_nr] = {
            "order_id": f"MOCK-ID-{order_nr}",
            "found_boms": found_boms
        }
    return results

def get_mock_check_feasibility(bom_input: Union[BillOfMaterials, list, str, dict], order_amount: int = 1) -> str:
    """
    Dynamically check feasibility for the input BOM.
    Crucial for handling different PDF extractions (Test_1 vs MOCK-Drawing).
    """
    
    # 1. Parse Input into a uniform list of dicts
    items = []
    
    if isinstance(bom_input, BillOfMaterials):
        for item in bom_input.items:
            items.append({
                 "p_num": item.part_number, 
                 "sku": item.item_nr, # Extract SKU
                 "desc": item.description, 
                 "qty": item.quantity or 1
            })
    elif isinstance(bom_input, list):
        for item in bom_input:
            if isinstance(item, BOMItem):
                 items.append({
                     "p_num": item.part_number, 
                     "sku": item.item_nr, 
                     "desc": item.description, 
                     "qty": item.quantity or 1
                })
            elif isinstance(item, dict):
                 items.append({
                     "p_num": item.get("part_number") or item.get("nummer") or "UNK",
                     "sku": item.get("item_nr") or item.get("nummer") or item.get("part_number"), # Try to find SKU
                     "desc": item.get("description") or item.get("name") or "Unknown Part",
                     "qty": item.get("quantity") or item.get("menge") or 1
                 })
    elif isinstance(bom_input, str):
        bom_str = bom_input.strip()
        if bom_str.startswith("BOM_"):
            from backend.src.store import BOMStore
            store = BOMStore()
            stored_data = store.get_bom(bom_str)
            if stored_data:
                bom_obj = stored_data["bom"]
                for item in bom_obj.items:
                    items.append({
                        "p_num": item.part_number, 
                        "sku": item.item_nr,
                        "desc": item.description, 
                        "qty": item.quantity or 1
                    })
            else:
                items.append({"p_num": bom_input, "sku": bom_input, "desc": "Product from ID (Not Found)", "qty": 1})
        else:
            # Maybe an ID/SKU? Treat the input string as the SKU.
            items.append({"p_num": bom_input, "sku": bom_input, "desc": "Product from ID", "qty": 1})
    
    if not items:
        # Fallback if parsing failed or empty
        return json.dumps({
            "feasible": False, 
            "error": "Empty BOM input in mock mode.", 
            "details": []
        })

    # 2. Generate Results
    details = []
    missing_items = []
    warnings = []
    overall_feasible = True

    for i in items:
        p_num = str(i.get("p_num", ""))
        sku = str(i.get("sku", "")) # Extract SKU
        name = str(i.get("desc", ""))
        qty_single = float(i.get("qty", 1) or 1)
        total_req = qty_single * order_amount
        
        # Generate status
        status = _generate_mock_part_status(p_num, name, total_req, sku=sku)
        
        # Update status with correct scaler values
        status["required_per_unit"] = qty_single
        status["total_required"] = total_req
        
        details.append(status)
        
        if not status["feasible"]:
            overall_feasible = False
            missing_items.append(status)
        
        if status["warning"]:
            warnings.append({"part": f"{p_num} ({name})", "message": status["warning"]})

    return json.dumps({
        "feasible": overall_feasible,
        "missing_items": missing_items,
        "warnings": warnings,
        "details": details,
        "source": "MOCK_DATA_DYNAMIC"
    }, indent=2)

def get_mock_bom_check(product_id: str) -> str:
    """Mock BOM check response."""
    # Deterministic yes/no
    is_bom = _hash_str_to_int(product_id) % 2 == 0
    
    if is_bom:
        count = (_hash_str_to_int(product_id) % 20) + 1
        return (
            f"CASE3: Artikel '{product_id}' (Mock Product) is a BOM "
            f"with {count} components. OK. [MOCK]"
        )
    else:
        return (
            f"CASE2: Artikel '{product_id}' (Mock Product) has NO components. "
            f"Should we add some? [MOCK]"
        )
