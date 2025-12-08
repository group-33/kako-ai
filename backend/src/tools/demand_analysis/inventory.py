"""Inventory and procurement context helpers for demand analysis tools."""
from __future__ import annotations

import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dateutil.relativedelta import relativedelta

from backend.src.config import XENTRAL_API_KEY, XENTRAL_BASE_URL, XENTRAL_TIMEOUT_SECONDS
from backend.src.models import BillOfMaterials

def _build_headers() -> Dict[str, str]:
    """Build authorization headers for Xentral API calls."""
    return {
        "Authorization": f"Bearer {XENTRAL_API_KEY or 'missing'}",
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


def get_inventory_for_part(part_number: str) -> Dict[str, Any]:
    """Return stock info for a single part (mocked)."""
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
    if not XENTRAL_API_KEY or not XENTRAL_BASE_URL:
        return {"message": f"Mock orders for next {time_quantity} {time_unit}", "orders": []}
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
    data = resp.json() if resp.content else []
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def get_future_boms(time_quantity: str, time_unit: str) -> Dict[str, Any]:
    """Aggregate BOMs for products in upcoming sales orders for a future window."""
    if not XENTRAL_API_KEY or not XENTRAL_BASE_URL:
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
