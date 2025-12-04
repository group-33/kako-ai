"""BOM-related API Tools"""
from __future__ import annotations

import json
import dspy
import requests
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from backend.src.models import BillOfMaterials

from backend.src.config import XENTRAL_BEARER_TOKEN, XENTRAL_BASE_URL

class BOMCheck(dspy.Signature):
    """Determine if the requested product is a Bill-of-Materials."""
    #Define the input/outvariables
    product_id = dspy.InputField(desc="")

def bom_check(product_identifier: str):
    """
    Docstring for bom_check
    
    :param product_id: Description
    :type product_id: str
    """

    #API REQUEST FOR ALL PRODUCTS
     #Have a list of products
    products = []
        #Go through all pages with size 1000
    #out = requests.get(url=XENTRAL_BASE_URL+"/api/v1/artikel?items=1000") #1000 products, We also max pages
    #products.append(out.json())
    #For page in range(2, max_pages):
        # out = request.get(url=XENTRAL_BASE_URL+f"/api/v2/products?items=1000&{page}")

    

    #MATCHING -> PERFECT(IN FUTURE FUZZY MATCHING)
    #FIND THE MATCHING ID
    #API REQUEST WITH ID TO GET PRODUCT INFORMATION
    #CHECK IF BOM EXISTS OR NOT
    #RETURN

def get_all_products():
    products = []
    headers_auth = {
    "Authorization": f"Bearer {XENTRAL_BEARER_TOKEN}"
}
    out = requests.get(url=f"{XENTRAL_BASE_URL}/api/v1/artikel?items=1000", headers=headers_auth).json()

    page_last = out['pagination']['page_last']

    products.extend(out['data'])

    for i in range(2, page_last + 1):
        out = requests.get(url=f"{XENTRAL_BASE_URL}/api/v1/artikel?items=1000&page={i}", headers=headers_auth).json()
        products.extend(out['data'])
    return products

def perform_bom_matching(bom: BillOfMaterials) -> str:
    store = ProductInfoStore()
    store.ensure_initialized()

    items_list = bom.items if hasattr(bom, 'items') else bom

    report_lines = []
    matches_found = 0

    report_lines.append(f"--- XENTRAL INTEGRATION PROPOSAL ---")

    for item in items_list:
        part_number = getattr(item, 'part_number', None)
        o_number = getattr(item, 'order_number', None)
        desc = getattr(item, 'description_of_part', None)

        match = store.search(bom_number=o_number, bom_desc=desc)

        if match != None:
            report_lines.append(
                f"✅ MATCH: BOM '{part_number}' -> Found Nummer {match.get('nummer')} ({match.get('name_de')})"
            )
        else:
            report_lines.append(f"❌ NO MATCH: BOM '{part_number}'")
    report_lines.append(f"-------------------------------")
    #report_lines.append(f"Summary: {matches_found}/{len(items_list)} items matched.")
    
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
                p_name = str(p.get('name_de') or "")
                p_desc = str(p.get('beschreibung_de') or "")
                p_short = str(p.get('kurztext_de') or "")
                text = f"{p_name} {p_short} {p_desc}"
                searchable_docs.append(text)

            if searchable_docs:
                embeddings = self.encoder.encode(searchable_docs)
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(np.array(embeddings))
            self.initialized = True


    def search(self, bom_number, bom_desc):
        #id_matches = []
        #text_matches = []

        seen_ids = set()

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
                    match['_source'] = "ID_MATCH" #Metadata for LLLM
                    return match

                if q_desc in p_name or q_desc in p_desc:
                    match = p.copy()
                    match['_source'] = "TEXT_MATCH"
                    return match

        if not has_specific_id:
            query_vector = self.encoder.encode([q_desc])
            distances, indices = self.index.search(np.array(query_vector), k=1)
            idx = indices[0][0]
            if idx != -1 and idx < len(self.products):
                match = self.products[idx].copy()
                match['_source'] = "VECTOR_MATCH (Semantic)"
                return match

        #final_results = id_matches + text_matches
        #return final_results[:limit]
        return None
