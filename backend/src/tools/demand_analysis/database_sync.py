import psycopg2
import urllib.parse
import requests
from typing import Any, Dict, List, Optional, Tuple
from backend.src.config import SUPABASE_PASSWORD, XENTRAL_BASE_URL, XENTRAL_BEARER_TOKEN, XENTRAL_TIMEOUT_SECONDS
import socket

from backend.src.tools.demand_analysis.embeddings import get_vertex_embedding

SUPABASE_DSN = f"postgresql://postgres.lnnlghymsockmysbbour:{SUPABASE_PASSWORD}@aws-1-eu-north-1.pooler.supabase.com:5432/postgres"
#Gets all products from Xentral API
def get_all_products() -> List[Dict[str, Any]]:
    products: List[Dict[str, Any]] = []
    headers_auth = {"Authorization": f"Bearer {XENTRAL_BEARER_TOKEN or ''}"}

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
    print("Done with Product Retrieval!")
    return products

#Syncs Supabase DB with Xentral
def db_sync():
    conn = psycopg2.connect(SUPABASE_DSN)
    print("Connected!")
    cursor = conn.cursor()

    prods = get_all_products()

    count = 0
    updated = 0

    for p in prods:
        x_id = p.get("id")
        x_num = p.get("nummer")
        x_name = str(p.get('name_de') or '')
        x_short = str(p.get('kurztext_de') or '')
        x_desc = str(p.get('anabregs_text') or '')
        x_bom_flag = p.get('stueckliste')

        semantic_text = x_desc.strip() 
        embedding = get_vertex_embedding(semantic_text)
        if x_num == "KAKO-0001996":
            print(x_name)

        sql = """
            INSERT INTO xentral_products 
            (xentral_id, nummer, name_de, kurztext_de, beschreibung_de, stueckliste, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (xentral_id) 
            DO UPDATE SET 
                nummer = EXCLUDED.nummer,
                name_de = EXCLUDED.name_de,
                kurztext_de = EXCLUDED.kurztext_de,
                beschreibung_de = EXCLUDED.beschreibung_de,
                stueckliste = EXCLUDED.stueckliste,
                embedding = EXCLUDED.embedding;
        """
        
        cursor.execute(sql, (
            x_id, x_num, x_name, x_short, x_desc, x_bom_flag, embedding
        ))
        
        count += 1
        updated += 1

        if count % 100 == 0:
            conn.commit()

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Sync Complete! {updated} products are now in Supabase.")


if __name__ == "__main__":
    db_sync()
