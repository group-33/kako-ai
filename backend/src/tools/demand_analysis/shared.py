"""Shared database stores to avoid circular imports."""
from __future__ import annotations
import psycopg2
from backend.src.config import SUPABASE_DSN

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
