"""BOM-related API tools (Xentral lookups and matching)."""
from __future__ import annotations

import dspy
import json
import psycopg2

from backend.src.models import BillOfMaterials
from backend.src.config import SUPABASE_PASSWORD, DB_HOST, DB_PORT, DB_USER, DB_NAME
from backend.src.tools.demand_analysis.embeddings import get_vertex_embedding
from backend.src.tools.demand_analysis.inventory import _fetch_bom_for_product

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
                
        cursor.close()
        conn.close()
        return None
