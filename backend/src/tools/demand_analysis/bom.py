"""BOM-related API tools (Xentral lookups and matching)."""
from __future__ import annotations

import dspy
import json
import psycopg2

from backend.src.models import BillOfMaterials
from backend.src.config import SUPABASE_PASSWORD
from backend.src.tools.demand_analysis.embeddings import get_vertex_embedding
from backend.src.tools.demand_analysis.inventory import _fetch_bom_for_product, get_inventory_for_product

DB_HOST = "aws-1-eu-north-1.pooler.supabase.com"
DB_PORT = "5432"
DB_USER = "postgres.lnnlghymsockmysbbour"
DB_NAME = "postgres"

SUPABASE_DSN = f"postgresql://{DB_USER}:{SUPABASE_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

class BOMCheck(dspy.Signature):
    """Determine if the requested product is a Bill-of-Materials."""

    product_id = dspy.InputField(desc="")


def bom_check(product_identifier: str) -> str:
    """
    Check whether a given product (by number or name) has an associated BOM in Xentral.

    The follow-up actions for CASE1/CASE2 are left as simple strings for now.
    """
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


def perform_bom_matching(bom: BillOfMaterials) -> str:
    """
    Matches extracted BOM items against the internal Xentral ERP product database.
    
    This tool takes a raw Bill of Materials (BOM) and performs a hybrid search 
    (Exact ID Match -> Text Substring -> Semantic Vector Search) for each item 
    to find its corresponding Xentral SKU.

    Args:
        bom (BillOfMaterials): The structured BOM object extracted from a technical drawing.

    Returns:
        str: A JSON-formatted string containing a list of items. Each item includes:
             - 'bom_part_id': The position number from the drawing.
             - 'extracted_number': The raw order number found in the BOM.
             - 'match_found': Boolean indicating if a database match was found.
             - 'xentral_number': The matched ERP SKU (if found).
             - 'xentral_name': The matched ERP Product Name.
             - 'confidence_source': How the match was found (e.g., 'ID_MATCH', 'VECTOR_MATCH').
    """
    store = ProductInfoStore()

    items_list = bom.items if hasattr(bom, "items") else bom

    results = []

    for item in items_list:
        part_number = getattr(item, "part_number", None)
        number = getattr(item, "item_nr", None)
        desc = getattr(item, "description", None)
        unit = getattr(item, "unit", None)
        quantity = getattr(item, "quantity", None)

        match = store.search(bom_number=number, bom_desc=desc)

        entry = {
            "bom_part_id": part_number,         
            "extracted_number": str(number) if number else None,
            "extracted_description": desc,
            "unit": unit,
            "quantity": quantity,
            "match_found": False,
            "xentral_number": None,
            "xentral_name": None,
            "confidence_source": None
        }

        if match:
            entry.update({
                "match_found": True,
                "xentral_number": match.get('nummer'),
                "xentral_name": match.get('name_de'),
                "confidence_source": match.get('_source')
            })
        
        results.append(entry)

    return json.dumps(results, indent=2)


class ProductInfoStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProductInfoStore, cls).__new__(cls)
            cls._instance.dsn = SUPABASE_DSN
        return cls._instance

    def _get_conn(self):
        return psycopg2.connect(self.dsn)
    
    def _normalize(self, text):
        if not text:
            return ""
        return str(text).replace(" ", "").lower()

    def search(self, bom_number, bom_desc):
        num_raw = str(bom_number).strip()
        q_num = self._normalize(num_raw)
        input_len = len(q_num)

        q_desc = str(bom_desc).strip().lower()
        has_specific_id = (len(q_num) > 0) and (q_num != "0")

        conn = self._get_conn()
        cursor = conn.cursor()

        if has_specific_id:
            # Check for exact internal ID match first if input looks numeric and short-ish
            if q_num.isdigit():
                 cursor.execute("SELECT xentral_id, nummer, name_de FROM xentral_products WHERE xentral_id = %s LIMIT 1", (q_num,))
                 row = cursor.fetchone()
                 if row:
                     return {"id": row[0], "nummer": row[1], "name_de": row[2], "_source": "EXACT_ID_MATCH"}

            cursor.execute("""
            SELECT xentral_id, nummer, name_de
            FROM xentral_products
            WHERE
                (
                (LENGTH(nummer) > 0 AND STRPOS(%s, REPLACE(LOWER(nummer), ' ', '')) > 0)
                AND (LENGTH(REPLACE(nummer, ' ', ''))::float / %s::float) > 0.5
                OR
                (LENGTH(name_de) > 0 AND STRPOS(%s, REPLACE(LOWER(name_de), ' ', '')) > 0)
                AND (LENGTH(REPLACE(nummer, ' ', ''))::float / %s::float) > 0.5
                )
            ORDER BY LENGTH(nummer) DESC
            LIMIT 1
            """, (q_num, input_len, q_num, input_len))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "nummer": row[1], "name_de": row[2], "_source": "ID_MATCH"}
            
            cursor.execute("""
            SELECT xentral_id, nummer, name_de
            FROM xentral_products
            WHERE LOWER(name_de) LIKE %s OR LOWER(beschreibung_de) LIKE %s
            LIMIT 1
            """, (f"%{num_raw}%", f"%{num_raw}%"))
            row = cursor.fetchone()
            if row:
                cursor.close()
                conn.close()
                return {"id": row[0], "nummer": row[1], "name_de": row[2], "_source": "ID_FOUND_IN_TEXT"}
            
        if len(q_desc) > 3:
                cursor.execute("""
                    SELECT xentral_id, nummer, name_de 
                    FROM xentral_products 
                    WHERE LOWER(name_de) LIKE %s
                    LIMIT 1
                """, (f"%{q_desc}%",))
                row = cursor.fetchone()
                if row:
                    cursor.close()
                    conn.close()
                    return {"id": row[0], "nummer": row[1], "name_de": row[2], "_source": "TEXT_MATCH"}
                
        if len(q_desc) > 3:
                query_vector = get_vertex_embedding(q_desc)
                
                cursor.execute("""
                    SELECT xentral_id, nummer, name_de 
                    FROM xentral_products 
                    ORDER BY embedding <-> %s::vector
                    LIMIT 1
                """, (query_vector,))
                
                row = cursor.fetchone()
                if row:
                    cursor.close()
                    conn.close()
                    return {"id": row[0], "nummer": row[1], "name_de": row[2], "_source": "VECTOR_MATCH"}
        cursor.close()
        conn.close()
        return None

def check_feasibility(bom_input: dict | list | str, order_amount: int) -> str:
    """
    Check if an order can be fulfilled based on BOM and current inventory.

    Args:
        bom_input: either a BOM structure (list of items), a product ID (str), or a dict with item details.
        order_amount: number of parent products ordered.

    Returns:
        JSON string report on feasibility.
    """
    results = {
        "feasible": True,
        "missing_items": [],
        "details": []
    }

    # Normalize input to a list of items
    items = []
    parent_product_name = "Unknown Product"

    # Case 1: Input is a Product ID (str)
    if isinstance(bom_input, str):
        # validation/lookup via Supabase or existing helper
        store = ProductInfoStore()
        # Clean ID
        p_id_raw = bom_input.strip()
        
        # Try to match if it's not a clear ID (e.g. if it's a name)
        match = store.search(bom_number=p_id_raw, bom_desc=p_id_raw)
        if match:
            product_id = match.get("id") or match.get("product_id")
            parent_product_name = match.get("name_de") or match.get("name") or p_id_raw
            
            # Fetch BOM
            fetched_bom = _fetch_bom_for_product(str(product_id))
            if fetched_bom:
                items = fetched_bom
            else:
                 # If no BOM, maybe it's a direct article? 
                 # We can treat it as a single item list where the item is the product itself.
                 items = [{
                     "artikel": product_id,
                     "nummer": match.get("nummer"),
                     "name_de": parent_product_name,
                     "menge": 1 # 1 per parent
                 }]
        else:
            return json.dumps({"error": f"Product '{bom_input}' not found in database."})

    # Case 2: Input is List of items (already resolved BOM)
    elif isinstance(bom_input, list):
         items = bom_input

    # Case 3: Input is Dict (BOM object)
    elif isinstance(bom_input, dict):
        if "items" in bom_input:
            items = bom_input["items"]
        else:
             # Maybe a single item dict?
             items = [bom_input]

    if not items:
        return json.dumps({"error": "No BOM items found to check."})

    for item in items:
        # Extract item details. Structure depends on source (Xentral API vs our internal BOM model)
        
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
            xentral_id = item.get("artikel") or item.get("product_id") or item.get("id")
            part_number = item.get("nummer") or item.get("part_number")
            name = item.get("name_de") or item.get("bezeichnung") or item.get("description") or item.get("name")
            qty_value = item.get("menge") or item.get("quantity") or item.get("amount") or 1.0
        
        # Quantity per unit
        try:
            qty_per_unit = float(qty_value)
        except (ValueError, TypeError):
            qty_per_unit = 1.0

        required_total = qty_per_unit * order_amount
        
        # Check stock
        stock = None
        if xentral_id:
            stock = get_inventory_for_product(str(xentral_id))
        else:
            # If we don't have an ID, we can't check stock reliably. 
            # Try to resolve via part_number if available?
            if part_number:
                 store = ProductInfoStore()
                 match = store.search(bom_number=part_number, bom_desc=name)
                 if match and match.get("id"):
                     xentral_id = match.get("id")
                     stock = get_inventory_for_product(str(xentral_id))
        
        # Handle stock result
        if stock is None:
             is_enough = False
             stock_display = "Unknown (Error)"
        else:
             is_enough = stock >= required_total
             stock_display = stock
        
        item_status = {
            "part_number": part_number,
            "name": name,
            "required_per_unit": qty_per_unit,
            "total_required": required_total,
            "in_stock": stock_display,
            "feasible": is_enough
        }
        
        results["details"].append(item_status)
        
        if not is_enough:
            results["feasible"] = False
            results["missing_items"].append(item_status)

    return json.dumps(results, indent=2)
