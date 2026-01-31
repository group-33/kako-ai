"""Inventory and procurement context helpers for demand analysis tools."""
from __future__ import annotations

import requests
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dateutil.relativedelta import relativedelta
import json

from backend.src.config import XENTRAL_BEARER_TOKEN, XENTRAL_BASE_URL, XENTRAL_TIMEOUT_SECONDS
from backend.src.models import BillOfMaterials
from backend.src.store import BOMStore


def _resolve_bom_argument(bom_input: Union[BillOfMaterials, str]) -> Optional[BillOfMaterials]:
    """Helper to resolve a BOM from an object or an ID string."""
    if isinstance(bom_input, BillOfMaterials):
        return bom_input
    
    if isinstance(bom_input, str):
        # 1. Try Store
        if bom_input.startswith("BOM_"):
            store = BOMStore()
            stored = store.get_bom(bom_input)
            if stored:
                print(f"--- [Inventory] Resolved BOM from Store: {bom_input} ---")
                return stored["bom"]
            else:
                print(f"--- [Inventory] Error: BOM ID {bom_input} not found in store. ---")
                return None
        
        # 2. Try parsing as JSON (fallback)
        try:
            data = json.loads(bom_input)
            # Basic validation
            if "items" in data:
                 # Reconstruct (simplified)
                 # Note: This is risky, but supports legacy calls
                 pass
        except:
            pass
            
    return None

def _build_headers() -> Dict[str, str]:
    """Build authorization headers for Xentral API calls."""
    return {
        "Authorization": f"Bearer {XENTRAL_BEARER_TOKEN or 'missing'}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _calculate_dates(time_quantity: str, time_unit: str) -> Tuple[str, str]:
    """Calculate ISO date range for a future window given a quantity and unit."""
    today_obj = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    quantity = int(time_quantity)
    unit = time_unit.lower()
    if unit in ["tag", "tage", "day", "days"]:
        end_date_obj = today_obj + timedelta(days=quantity)
    elif unit in ["woche", "wochen", "week", "weeks"]:
        end_date_obj = today_obj + timedelta(weeks=quantity)
    elif unit in ["monat", "monate", "month", "months"]:
        end_date_obj = today_obj + relativedelta(months=quantity)
    else:
        raise ValueError(f"Invalid time unit: {time_unit}")
    return today_obj.isoformat(timespec="minutes"), end_date_obj.isoformat(timespec="minutes")


# --- Public functions --------------------------------------------------------

def get_inventory_for_product(product_id: str) -> Optional[dict]:
    """
    Fetch current stock quantity and minimum stock for a product from Xentral.
    
    Args:
        product_id: The Xentral internal ID of the product OR the product number (Nummer).
        
    Returns:
        Optional[dict]: Dict with 'stock' (int/float) and 'min_stock' (int/float). Returns None if error.
    """
    if not XENTRAL_BEARER_TOKEN or not XENTRAL_BASE_URL:
        # Fallback to mock if no credentials
        return {"stock": 125, "min_stock": 10}

    # Helper to parse response data
    def parse_inventory_data(product_data):
        # 'lagerbestand' is a dict containing 'verkaufbar' (sellable stock)
        lb = product_data.get("lagerbestand", {})
        if isinstance(lb, dict):
            stock = lb.get("verkaufbar", 0)
        else:
            stock = lb # Fallback if it is a number
        
        # Fetch minimum stock (mindestlager)
        min_stock = product_data.get("mindestlager", 0)
        
        return {
            "stock": int(float(stock)), 
            "min_stock": int(float(min_stock))
        }

    # Strategy 1: Direct ID Lookup (Most likely for 'product_id')
    # Endpoint: /api/v1/artikel/{id}
    url_direct = f"{XENTRAL_BASE_URL}/api/v1/artikel/{product_id}"
    params_direct = {"include": "lagerbestand"}
    
    try:
        resp = requests.get(url_direct, params=params_direct, headers=_build_headers(), timeout=XENTRAL_TIMEOUT_SECONDS)
        if resp.status_code == 200:
             data = resp.json()
             # Direct ID often returns the object directly or wrapped in data
             item = data.get("data") if "data" in data else data
             # If it's a list (rare for ID endpoint but possible), take first
             if isinstance(item, list) and len(item) > 0:
                 item = item[0]
             
             if isinstance(item, dict) and "id" in item:
                 return parse_inventory_data(item)
    except Exception as e:
        print(f"Debug: Direct ID lookup for {product_id} failed: {e}")

    # Strategy 2: Search by 'nummer' (Fallback if product_id is actually a SKU like 'KAKO-ST-XXX')
    url_search = f"{XENTRAL_BASE_URL}/api/v1/artikel"
    params_search = {
        "filter[0][property]": "nummer",
        "filter[0][expression]": "eq",
        "filter[0][value]": product_id,
        "include": "lagerbestand",
        "items": 1
    }
    
    try:
        resp = requests.get(url_search, params=params_search, headers=_build_headers(), timeout=XENTRAL_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", [])
        if items:
            return parse_inventory_data(items[0])
            
    except Exception as e:
        print(f"Error fetching inventory for {product_id} (Search Strategy): {e}")
        return None
        
    return None


def get_sales_orders(time_quantity: str, time_unit: str) -> Any:
    """Return sales orders for the given future time window. Real call if creds present, else mock."""
    print(f"--- [Inventory] Fetching Sales Orders (Next {time_quantity} {time_unit}) ---")

    from_date, to_date = _calculate_dates(time_quantity, time_unit)
    url = f"{XENTRAL_BASE_URL}/api/v1/belege/auftraege"
    params = {
        "filter[0][property]": "tatsaechlichesLieferdatum",
        "filter[0][expression]": "gte",
        "filter[0][value]": from_date,
        "filter[1][property]": "tatsaechlichesLieferdatum",
        "filter[1][expression]": "lte",
        "filter[1][value]": to_date,
        "include": "positionen",
        "items": 1000,
    }
    print(params)
    resp = requests.get(url, params=params, headers=_build_headers(), timeout=XENTRAL_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json() if resp.content else {}
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def get_future_boms(time_quantity: str, time_unit: str) -> Dict[str, Any]:
    """Aggregate BOMs for products in upcoming sales orders for a future window."""
    print(f"--- [Inventory] Get Future BOMs (Next {time_quantity} {time_unit}) ---")

    if not XENTRAL_BEARER_TOKEN or not XENTRAL_BASE_URL:
        return {
            "summary": f"[MOCK] No credentials; returning empty BOM list for next {time_quantity} {time_unit}",
            "details": [],
        }
    from_date, to_date = _calculate_dates(time_quantity, time_unit)
    try:
        orders = get_sales_orders(time_quantity, time_unit)
    except Exception as exc:
        return {"error": f"Failed to fetch orders: {exc}"}
    if not orders:
        return {"message": f"No orders found between {from_date} and {to_date}."}

    product_map: Dict[str, Optional[str]] = {}
    for order in orders:
        positions = order.get("positionen", []) or []
        for pos in positions:
            p_id = pos.get("artikel") or pos.get("produkt") or pos.get("artikel_id")
            p_name = pos.get("artikel_bezeichnung") or pos.get("bezeichnung")
            if p_id:
                product_map[str(p_id)] = p_name

    results = []
    for p_id, p_name in product_map.items():
        bom_components = _fetch_bom_for_product(p_id)
        if bom_components:
            results.append(
                {
                    "parent_product_id": p_id,
                    "parent_product_name": p_name,
                    "bom_components": bom_components,
                }
            )

    if not results:
        return {
            "message": (
                "Orders found, but no associated Bill of Materials (Stücklisten) "
                "could be retrieved. Products may be simple articles."
            )
        }

    return {
        "summary": f"Found {len(results)} products with BOMs for orders between {from_date} and {to_date}",
        "details": results,
    }


def get_orders_by_customer(customer_id: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """
    Fetch orders for a specific customer within a date range.
    
    Args:
        customer_id: The customer number (Kundennummer) or customer ID.
        start_date: Start date (YYYY-MM-DD), defaults to 1 month ago.
        end_date: End date (YYYY-MM-DD), defaults to today.
    """
    print(f"--- [Inventory] Get Orders By Customer: {customer_id} ---")

    if not start_date:
        start_date = (datetime.now() - relativedelta(months=1)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    url = f"{XENTRAL_BASE_URL}/api/v1/belege/auftraege"
    params = {
        "filter[0][property]": "kundennummer",
        "filter[0][expression]": "eq",
        "filter[0][value]": customer_id,
        "filter[1][property]": "tatsaechlichesLieferdatum",
        "filter[1][expression]": "gte",
        "filter[1][value]": start_date,
        "filter[2][property]": "tatsaechlichesLieferdatum",
        "filter[2][expression]": "lte",
        "filter[2][value]": end_date,
        "include": "positionen",
        "items": 100,
    }
    
    try:
        resp = requests.get(url, params=params, headers=_build_headers(), timeout=XENTRAL_TIMEOUT_SECONDS)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        return [{"error": f"Failed to fetch orders for customer {customer_id}: {str(e)}"}]


def get_boms_for_orders(order_numbers: List[str]) -> Dict[str, Any]:
    """
    Retrieve BOMs for all products contained in the specified orders.
    
    Args:
        order_numbers: List of order numbers (Belegnummer, e.g., 'AT-2024-059561').
    """
    print(f"--- [Inventory] Get BOMs for Orders: {str(order_numbers)} ---")

    results = {}
    
    for order_nr in order_numbers:
        # Fetch order to get positions
        url = f"{XENTRAL_BASE_URL}/api/v1/belege/auftraege"
        params = {
            "filter[0][property]": "belegnr",
            "filter[0][expression]": "eq",
            "filter[0][value]": order_nr,
            "include": "positionen",
            "items": 1
        }
        
        try:
            resp = requests.get(url, params=params, headers=_build_headers(), timeout=XENTRAL_TIMEOUT_SECONDS)
            if resp.status_code == 404:
                results[order_nr] = {"error": "Order not found (404)"}
                continue
            resp.raise_for_status()
            data = resp.json()
            orders = data.get("data", [])
            
            if not orders:
                results[order_nr] = {"error": "Order not found"}
                continue
                
            order = orders[0]
            positions = order.get("positionen", [])
            order_boms = []
            
            for pos in positions:
                article_id = pos.get("artikel")
                article_num = pos.get("nummer")
                
                if article_id:
                    bom = _fetch_bom_for_product(str(article_id))
                    if bom:
                        order_boms.append({
                            "product_number": article_num,
                            "product_id": article_id,
                            "bom": bom
                        })
            
            results[order_nr] = {
                "order_id": order.get("id"),
                "found_boms": order_boms
            }
            
        except Exception as e:
            results[order_nr] = {"error": f"Failed to process order: {str(e)}"}
            
    return results

# --- Private Helpers (Internal) ----------------------------------------------

def _fetch_bom_for_product(product_id: str) -> List[Dict[str, Any]]:
    url = f"{XENTRAL_BASE_URL}/api/v1/products/{product_id}/parts"
    try:
        resp = requests.get(url, headers=_build_headers(), timeout=XENTRAL_TIMEOUT_SECONDS)
        resp.raise_for_status()
        if not resp.content:
            return []
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []
