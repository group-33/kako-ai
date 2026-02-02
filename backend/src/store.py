from typing import Dict, Optional, Any
from backend.src.models import BillOfMaterials

class BOMStore:
    _instance = None
    _boms: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BOMStore, cls).__new__(cls)
        return cls._instance

    def save_bom(self, bom_id: str, bom: BillOfMaterials, source_document: str = ""):
        """Store a BOM in memory."""
        self._boms[bom_id] = {
            "bom": bom,
            "source_document": source_document
        }
        print(f"--- [BOMStore] Saved BOM {bom_id} to memory. ---")

    def get_bom(self, bom_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a BOM by ID."""
        return self._boms.get(bom_id)

    def list_boms(self) -> Dict[str, Any]:
        return self._boms


class ProcurementStore:
    """Store for caching large procurement API results to avoid passing them to LLM."""
    _instance = None
    _searches: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcurementStore, cls).__new__(cls)
        return cls._instance

    def save_search_result(self, data: Any) -> str:
        """Store a search result and return an ID."""
        import uuid
        search_id = f"SEARCH_{uuid.uuid4().hex[:8].upper()}"
        self._searches[search_id] = data
        print(f"--- [ProcurementStore] Cached data under {search_id} ---")
        return search_id

    def get_search_result(self, search_id: str) -> Optional[Any]:
        """Retrieve a search result by ID."""
        return self._searches.get(search_id)
