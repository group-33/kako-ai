"""
Placeholder client for Xentral ERP API access.

Reference docs: https://developer.xentral.com/reference
This mock implementation focuses on shaping the interface that the
Demand Analyst agent expects. Replace the internals with real calls later.
"""
from __future__ import annotations

from typing import Dict, Any, List

from ..config import XENTRAL_API_KEY, XENTRAL_BASE_URL
from ..models import BillOfMaterials


class XentralClient:
    """Simple toolbox-like wrapper around Xentral endpoints."""

    def __init__(self) -> None:
        if not XENTRAL_API_KEY:
            print("WARNING: XENTRAL_API_KEY is not set. Using mock client.")
            self.api_key = "mock_key"
            self.base_url = "mock_url"
        else:
            self.api_key = XENTRAL_API_KEY
            self.base_url = XENTRAL_BASE_URL

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def available_tools(self) -> List[Dict[str, str]]:
        """Returns the set of callable tools for the DSPy router."""
        return [
            {
                "name": "run_full_feasibility_analysis",
                "description": (
                    "Performs a deep analysis of a BOM against inventory, "
                    "pending procurement, and existing sales orders."
                ),
                "parameters": "bom: BillOfMaterials, quantity_required: int",
            },
            {
                "name": "list_deliveries_in_range",
                "description": "Lists all incoming deliveries between start_date and end_date.",
                "parameters": "start_date: str (YYYY-MM-DD), end_date: str (YYYY-MM-DD)",
            },
            {
                "name": "get_inventory_for_part",
                "description": "Returns current stock levels for a single part number.",
                "parameters": "part_number: str",
            },
        ]

    # --- Tooling methods exposed to the agent ---
    def run_full_feasibility_analysis(
        self, bom: BillOfMaterials, quantity_required: int
    ) -> Dict[str, Any]:
        """Fetches all context data needed for a feasibility analysis."""
        print(f"[XentralClient MOCK] Running FULL feasibility for {quantity_required} units...")
        inventory = self.get_inventory_for_bom(bom)
        pending = self.get_pending_procurement_orders()
        existing = self.get_existing_customer_orders()
        return {
            "inventory": inventory,
            "pending_procurement": pending,
            "existing_orders": existing,
        }

    def list_deliveries_in_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Returns mocked procurement deliveries filtered by date window."""
        print(f"[XentralClient MOCK] Fetching deliveries between {start_date} and {end_date}...")
        return [
            {
                "order_id": "PO-1001",
                "part_number": "PN-EXT-456",
                "quantity": 50,
                "eta_date": "2025-11-28",
            }
        ]

    def get_inventory_for_part(self, part_number: str) -> Dict[str, Any]:
        """Returns mocked stock information for a single item."""
        print(f"[XentralClient MOCK] Checking stock for {part_number}...")
        return {"part_number": part_number, "in_stock": 125}

    # --- Helper methods (not surfaced as tools directly) ---
    def get_inventory_for_bom(self, bom: BillOfMaterials) -> Dict[str, Any]:
        """Simulates inventory results for all BOM items."""
        print(f"[XentralClient MOCK] Checking inventory for {len(bom.items)} items...")
        if not bom.items:
            return {}
        data = {item.part_number: {"in_stock": 100} for item in bom.items}
        first_part = bom.items[0].part_number
        data[first_part] = {"in_stock": 2}
        return data

    def get_pending_procurement_orders(self) -> List[Dict[str, Any]]:
        """Simulates lookup of open procurement orders."""
        print("[XentralClient MOCK] Fetching pending procurement orders...")
        return [
            {
                "part_number": "PN-EXT-456",
                "quantity": 50,
                "eta_date": "2025-11-30",
            }
        ]

    def get_existing_customer_orders(self) -> List[Dict[str, Any]]:
        """Simulates lookup of existing customer orders using similar parts."""
        print("[XentralClient MOCK] Fetching existing customer orders...")
        return [
            {
                "order_id": "CUST-1001",
                "due_date": "2025-11-20",
                "bom_id": "BOM-A",
            }
        ]
