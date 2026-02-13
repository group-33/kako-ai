"""BOM-related API tools (Xentral lookups and matching)."""
from __future__ import annotations

import dspy
import json
import psycopg2

from backend.src.models import BillOfMaterials
from backend.src.config import SUPABASE_PASSWORD, DB_HOST, DB_PORT, DB_USER, DB_NAME, SUPABASE_DSN
from backend.src.models import BillOfMaterials
from backend.src.tools.demand_analysis.shared import ProductInfoStore
from backend.src.tools.demand_analysis.inventory import _fetch_bom_for_product, get_inventory_for_product
from backend.src.auth_context import is_current_user_mock
from backend.src.tools.demand_analysis import mock_data


class BOMCheck(dspy.Signature):
    """Determine if the requested product is a Bill-of-Materials."""

    product_id = dspy.InputField(desc="")


def bom_check(product_identifier: str) -> str:
    """
    Check whether a given product (by number or name) has an associated BOM in Xentral.

    The follow-up actions for CASE1/CASE2 are left as simple strings for now.
    """
    if is_current_user_mock():
        return mock_data.get_mock_bom_check(product_identifier)

    print(f"--- [BOM Check] Verifying product: {str(product_identifier)} ---")

    query = (product_identifier or "").strip()
    if not query:
        return "No product identifier provided. Please pass an Artikelnummer or product name."

    store = ProductInfoStore()
    match = store.search(bom_number=query, bom_desc=query)
    if not match:
        return f"Could not find any matching product for '{query}'."

    product_id = match.get("id") or match.get("artikel") or match.get("product_id")
    product_num = match.get("nummer") or query
    product_name = match.get("name_de") or match.get("name_en") or ""

    if not product_id:
        return f"Matched '{product_num}' but no product ID is available to query its BOM."

    # Use the shared Xentral helper from the inventory module to fetch BOM parts.
    bom_parts = _fetch_bom_for_product(str(product_id))
    if bom_parts:
        return (
            f"CASE3: Artikel '{product_num}' ({product_name or 'kein Name'}) ist Stückliste "
            f"mit {len(bom_parts)} Stücklistenelement(en). PASST."
        )

    return (
        f"CASE2: Artikel '{product_num}' ({product_name or 'kein Name'}) hat keine Stücklistenelemente. "
        f"Sollen wir die Stücklistenelemente zufügen?"
    )


def perform_bom_matching(bom: BillOfMaterials) -> BillOfMaterials:
    """
    Matches extracted BOM items against the internal Xentral ERP product database.
    Finds the Xentral number.
    """
    store = ProductInfoStore()
    #print("in bom matching")

    for item in bom.items:
        # Search using the extracted item number and description
        match = store.search(bom_number=item.item_nr, bom_desc=item.description) #
        
        if match:
            item.xentral_number = match.get("nummer")
            #item.xentral_number = match.get("nummer")
            #item.match_source = match.get("_source")
        else:
            item.xentral_number = "NOT_FOUND"

    return bom


from backend.src.tools.demand_analysis.shared import ProductInfoStore

from pydantic import BaseModel
from typing import Union

def check_feasibility(bom_input: Union[BillOfMaterials, list, str], order_amount: int = 1) -> str:
    """
    Check if an order can be fulfilled based on BOM and current inventory.

    Args:
        bom_input: either a BOM structure (list of items), a product ID (str), or a list with item details.
        order_amount: number of parent products ordered.

    Returns:
        JSON string report on feasibility.
        Schema:
        {
            "feasible": bool,       # Overall feasibility
            "missing_items": [],    # List of items with insufficient stock
            "warnings": [           # List of warnings (e.g. stock low but feasible)
                {"part": str, "message": str}
            ],
            "details": []           # Full line-item details
        }
    """
    if is_current_user_mock():
        return mock_data.get_mock_check_feasibility(bom_input, order_amount)

    results = {
        "feasible": True,
        "missing_items": [],
        "warnings": [],
        "details": []
    }

    print(f"--- [Feasibility Check] Checking BOM: {bom_input} | Amount: {order_amount} ---")
    
    items = []
    parent_product_name = "Unknown Product"

    if isinstance(bom_input, str):
        bom_str = bom_input.strip()
        
        # Case A: It's a BOM Reference ID from the Store
        if bom_str.startswith("BOM_"):
            from backend.src.store import BOMStore
            store = BOMStore()
            stored_data = store.get_bom(bom_str)
            if stored_data:
                print(f"--- [Feasibility] Retrieved verified BOM from Store: {bom_str} ---")
                bom_obj = stored_data["bom"]
                items = bom_obj.items
                parent_product_name = bom_obj.title
            else:
                return json.dumps({"feasible": False, "error": f"BOM ID '{bom_str}' not found in memory. It may have expired."})
        
        # Case B: It's a Product ID (Legacy/Direct lookup)
        else:
            # Fallback to fetching BOM for ID for backward compatibility or direct ID usage
            fetched = _fetch_bom_for_product(bom_input)
            if fetched:
                items = fetched
            else:
                items = [{"xentral_id": bom_input, "quantity": 1, "name": "Single Item"}]
            
    elif isinstance(bom_input, BillOfMaterials):
        # Use the items directly from the model
        items = bom_input.items
        
    elif isinstance(bom_input, list):
        items = bom_input
    
    for item in items:
        # normalize fields based on input type (Model vs Dict)
        if isinstance(item, BaseModel): # Robust check for Pydantic
            # item is BOMItem from models.py (extracted from drawing).
            # It contains external identifiers (item_nr, description) which we must resolve to a Xentral Internal ID to check stock.
            
            qty_per_unit = float(item.quantity) if item.quantity else 1.0
            
            # Access fields directly as attributes
            item_nr = getattr(item, 'item_nr', None)
            start_pn = getattr(item, 'part_number', None)
            desc = getattr(item, 'description', None)
            
            # NEW: Check if xentral_number is already resolved/present
            pre_resolved_id = getattr(item, 'xentral_number', None)
            
            xentral_id = None
            name = desc or "Unknown"
            part_number = item_nr or str(start_pn)
            match_source = "SEARCH"
            
            if pre_resolved_id and pre_resolved_id != "NOT_FOUND":
                 # If we have it, assume it's the internal ID.
                 xentral_id = pre_resolved_id
                 match_source = "DIRECT"
            else:
                search_query = item_nr or str(start_pn) or desc
                
                # Try to resolve ID
                store = ProductInfoStore()
                match = store.search(bom_number=str(search_query), bom_desc=desc)
                
                xentral_id = match.get("id") if match else None
        else:
            # Dictionary input (Legacy path)
            # Default placeholders
            xentral_id = None
            part_number = None
            name = None
            qty_value = 1.0

            # Check for nested Xentral structure (item['product'] dict)
            if isinstance(item.get("product"), dict):
                prod = item["product"]
                xentral_id = prod.get("id")
                part_number = prod.get("number") or prod.get("nummer")
                name = prod.get("name") or prod.get("name_de")
                qty_value = item.get("amount") or item.get("menge") or 1.0
            else:
                # Fallback to flat structure (our model or simplified list)
                xentral_id = item.get("artikel") or item.get("product_id") or item.get("id") or item.get("xentral_id")
                part_number = item.get("nummer") or item.get("part_number")
                name = item.get("name_de") or item.get("bezeichnung") or item.get("description") or item.get("name")
                qty_value = item.get("menge") or item.get("quantity") or item.get("amount") or 1.0
            
            try:
                qty_per_unit = float(qty_value)
            except (ValueError, TypeError):
                qty_per_unit = 1.0

        required_total = qty_per_unit * order_amount
        
        # Check stock
        stock_info = None
        current_stock = 0
        min_stock = 0
        
        if xentral_id:
            stock_info = get_inventory_for_product(str(xentral_id))
        elif part_number:
             # Try second pass resolution if dict path failed
             store = ProductInfoStore()
             match = store.search(bom_number=part_number, bom_desc=name)
             if match and match.get("id"):
                 xentral_id = match.get("id")
                 stock_info = get_inventory_for_product(str(xentral_id))
                 
        # Handle stock result
        is_enough = False
        stock_display = "Unknown (Error)"
        warning_msg = None
        
        if stock_info:
            current_stock = stock_info.get("stock", 0)
            min_stock = stock_info.get("min_stock", 0)
            stock_display = current_stock
            
            is_enough = current_stock >= required_total
            
            # Check Minimum Stock Warning
            remaining_stock = current_stock - required_total
            if is_enough and remaining_stock < min_stock:
                warning_msg = f"Stock will fall below minimum! (Remaining: {remaining_stock}, Min: {min_stock})"
                results["warnings"].append({
                    "part": part_number or name,
                    "message": warning_msg
                })
        else:
             is_enough = False # Treat error/unknown as not feasible for safety

        item_status = {
            "part_number": part_number,
            "name": name,
            "required_per_unit": qty_per_unit,
            "total_required": required_total,
            "in_stock": stock_display,
            "min_stock": min_stock if stock_info else "Unknown",
            "feasible": is_enough,
            "warning": warning_msg
        }
        
        results["details"].append(item_status)
        
        if not is_enough:
            results["feasible"] = False
            results["missing_items"].append(item_status)
            
    return json.dumps(results, indent=2)
