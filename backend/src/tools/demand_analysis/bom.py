"""BOM-related API Tools"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import dspy
import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

from backend.src.models import BillOfMaterials
from backend.src.config import XENTRAL_API_KEY, XENTRAL_BASE_URL, XENTRAL_TIMEOUT_SECONDS


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
    store.ensure_initialized()

    match = store.search(bom_number=query, bom_desc=query)
    if not match:
        return f"Could not find any matching product for '{query}'."

    product_id = match.get("id") or match.get("artikel") or match.get("product_id")
    product_num = match.get("nummer") or query
    product_name = match.get("name_de") or match.get("name_en") or ""

    if not product_id:
        return f"Matched '{product_num}' but no product ID is available to query its BOM."

    bom_parts, error = _fetch_bom_parts(str(product_id))

    if error and bom_parts is None:
        return (
            f"CASE1: Keine Stückliste für Artikel '{product_num}' ({product_name or 'kein Name'}) "
            f"(Fehler: {error}). Sollen wir die Stückliste anlegen?"
        )

    if bom_parts:
        return (
            f"CASE3: Artikel '{product_num}' ({product_name or 'kein Name'}) ist Stückliste "
            f"mit {len(bom_parts)} Stücklistenelement(en). PASST."
        )

    return (
        f"CASE2: Artikel '{product_num}' ({product_name or 'kein Name'}) hat keine Stücklistenelemente. "
        f"Sollen wir die Stücklistenelemente zufügen?"
    )


def get_all_products() -> List[Dict[str, Any]]:
    products: List[Dict[str, Any]] = []
    headers_auth = {"Authorization": f"Bearer {XENTRAL_API_KEY or ''}"}

    # Go through all pages with size 1000
    out = requests.get(
        url=f"{XENTRAL_BASE_URL}/api/v1/artikel?items=1000",
        headers=headers_auth,
        timeout=XENTRAL_TIMEOUT_SECONDS,
    ).json()

    page_last = out["pagination"]["page_last"]

    products.extend(out["data"])

    for i in range(2, page_last + 1):
        out = requests.get(
            url=f"{XENTRAL_BASE_URL}/api/v1/artikel?items=1000&page={i}",
            headers=headers_auth,
            timeout=XENTRAL_TIMEOUT_SECONDS,
        ).json()
        products.extend(out["data"])
    return products


def _fetch_bom_parts(product_id: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Use the v1 endpoint to retrieve BOM parts for the product.

    Returns a tuple of (parts, error_message).
    """
    headers = {"Authorization": f"Bearer {XENTRAL_API_KEY or ''}"}
    url = f"{XENTRAL_BASE_URL}/api/v1/products/{product_id}/parts"
    try:
        resp = requests.get(url, headers=headers, timeout=XENTRAL_TIMEOUT_SECONDS)
        resp.raise_for_status()

        if not resp.content:
            return [], None

        data = resp.json()
        if isinstance(data, dict):
            if "data" in data:
                return data.get("data") or [], None
            if "parts" in data and isinstance(data.get("parts"), list):
                return data.get("parts"), None
        if isinstance(data, list):
            return data, None

        return [], None
    except Exception as exc:
        return None, str(exc)


def perform_bom_matching(bom: BillOfMaterials) -> str:
    store = ProductInfoStore()
    store.ensure_initialized()

    items_list = bom.items if hasattr(bom, "items") else bom

    report_lines: List[str] = []
    report_lines.append("--- XENTRAL INTEGRATION PROPOSAL ---")

    for item in items_list:
        part_number = getattr(item, "part_number", None)
        o_number = getattr(item, "order_number", None)
        desc = getattr(item, "description_of_part", None)

        match = store.search(bom_number=o_number, bom_desc=desc)

        if match is not None:
            report_lines.append(
                f"[MATCH] BOM '{part_number}' -> Nummer {match.get('nummer')} ({match.get('name_de')})"
            )
        else:
            report_lines.append(f"[NO MATCH] BOM '{part_number}'")
    report_lines.append("-------------------------------")

    return "\n".join(report_lines)


class ProductInfoStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProductInfoStore, cls).__new__(cls)
            cls._instance.products = []
            cls._instance.initialized = False
            cls._instance.index = None
            cls._instance.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._instance

    def ensure_initialized(self):
        if not self.initialized:
            self.products = get_all_products()
            searchable_docs = []
            for p in self.products:
                p_name = str(p.get("name_de") or "")
                p_desc = str(p.get("beschreibung_de") or "")
                p_short = str(p.get("kurztext_de") or "")
                text = f"{p_name} {p_short} {p_desc}"
                searchable_docs.append(text)

            if searchable_docs:
                embeddings = self.encoder.encode(searchable_docs)
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(np.array(embeddings))
            else:
                self.index = None
            self.initialized = True

    def search(self, bom_number, bom_desc):
        q_num = str(bom_number).strip().lower()
        q_desc = str(bom_desc).strip().lower()
        has_specific_id = (len(q_num) > 0) and (q_num != "0")

        if has_specific_id:
            for p in self.products:
                p_num = str(p.get('nummer')).lower()
                p_name = str(p.get('name_de')).lower()
                p_desc = str(p.get('beschreibung_de')).lower()
                
                if  q_num in p_num or q_num in p_name:
                    match = p.copy()
                    match["_source"] = "ID_MATCH"
                    return match

                if q_desc in p_name or q_desc in p_desc:
                    match = p.copy()
                    match["_source"] = "TEXT_MATCH"
                    return match

        if not has_specific_id and self.index is not None and self.products:
            query_vector = self.encoder.encode([q_desc])
            distances, indices = self.index.search(np.array(query_vector), k=1)
            idx = indices[0][0]
            if idx != -1 and idx < len(self.products):
                match = self.products[idx].copy()
                match["_source"] = "VECTOR_MATCH (Semantic)"
                return match

        return None
