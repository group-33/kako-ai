"""Inventory and procurement context helpers for demand analysis tools."""
from __future__ import annotations

import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dateutil.relativedelta import relativedelta

from backend.src.config import XENTRAL_BEARER_TOKEN, XENTRAL_BASE_URL, XENTRAL_TIMEOUT_SECONDS
from backend.src.models import BillOfMaterials

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
def run_full_feasibility_analysis(bom: BillOfMaterials, quantity_required: int) -> Dict[str, Any]:
    """Fetch inventory, pending procurement, and existing orders for a BOM (mocked)."""
    inventory = get_inventory_for_bom(bom)
    pending = get_pending_procurement_orders()
    existing = get_existing_customer_orders()
    return {
        "inventory": inventory,
        "pending_procurement": pending,
        "existing_orders": existing,
    }


def list_deliveries_in_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """List incoming deliveries in the given date window (mocked)."""
    return [
        {
            "order_id": "PO-1001",
            "part_number": "PN-EXT-456",
            "quantity": 50,
            "eta_date": "2025-11-28",
        }
    ]


def get_inventory_for_product(product_id: str) -> Optional[dict]:
    """
    Fetch current stock quantity and minimum stock for a product from Xentral.
    
    Args:
        product_id: The Xentral internal ID of the product.
        
    Returns:
        Optional[dict]: Dict with 'stock' (int/float) and 'min_stock' (int/float). Returns None if error.
    """
    if not XENTRAL_BEARER_TOKEN or not XENTRAL_BASE_URL:
        # Fallback to mock if no credentials
        return {"stock": 125, "min_stock": 10}

    # Correct endpoint verified: /api/v1/artikel with include=lagerbestand
    url = f"{XENTRAL_BASE_URL}/api/v1/artikel"
    params = {
        "filter[0][property]": "id",
        "filter[0][expression]": "eq",
        "filter[0][value]": product_id,
        "include": "lagerbestand",
        "items": 1
    }
    
    try:
        resp = requests.get(url, params=params, headers=_build_headers(), timeout=XENTRAL_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", [])
        if items:
            product = items[0]
            # 'lagerbestand' is a dict containing 'verkaufbar' (sellable stock)
            lb = product.get("lagerbestand", {})
            if isinstance(lb, dict):
                stock = lb.get("verkaufbar", 0)
            else:
                stock = lb # Fallback if it is a number
            
            # Fetch minimum stock (mindestlager)
            min_stock = product.get("mindestlager", 0)
            
            return {
                "stock": int(float(stock)), 
                "min_stock": int(float(min_stock))
            }
    except Exception as e:
        print(f"Error fetching inventory for {product_id}: {e}")
        return None
        
    return None


def get_inventory_for_part(part_number: str) -> Dict[str, Any]:
    """Return stock info for a single part (mocked wrapper, useful for legacy compatibility)."""
    # Note: proper mapping from part_number to ID would be needed for real check
    return {"part_number": part_number, "in_stock": 125}


def get_inventory_for_bom(bom: BillOfMaterials) -> Dict[str, Any]:
    """Simulate inventory results for all BOM items."""
    if not bom.items:
        return {}
    data = {item.part_number: {"in_stock": 100} for item in bom.items}
    first_part = bom.items[0].part_number
    data[first_part] = {"in_stock": 2}
    return data


def get_pending_procurement_orders() -> List[Dict[str, Any]]:
    """Simulate lookup of open procurement orders."""
    return [
        {
            "part_number": "PN-EXT-456",
            "quantity": 50,
            "eta_date": "2025-11-30",
        }
    ]


def get_existing_customer_orders() -> List[Dict[str, Any]]:
    """Simulate lookup of existing customer orders using similar parts."""
    return [
        {
            "order_id": "CUST-1001",
            "due_date": "2025-11-20",
            "bom_id": "BOM-A",
        }
    ]


def get_sales_orders(time_quantity: str, time_unit: str) -> Any:
    """Return sales orders for the given future time window. Real call if creds present, else mock."""
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
    resp = requests.get(url, params=params, headers=_build_headers(), timeout=XENTRAL_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json() if resp.content else {}
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def get_future_boms(time_quantity: str, time_unit: str) -> Dict[str, Any]:
    """Aggregate BOMs for products in upcoming sales orders for a future window."""
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


# --- HTTP helper -------------------------------------------------------------
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
