from __future__ import annotations

import hashlib
import json
import os
import tempfile

import dspy

from backend.src.models import (
    ToolUseBlock,
    BOMRow,
    BOMTableData,
    BillOfMaterials,
    BOMUpdate,
)

def _bom_item_key(item, idx: int) -> str:
    order_number = getattr(item, "order_number", None)
    part_number = getattr(item, "part_number", None)
    if order_number is not None and part_number:
        return f"{order_number}:{part_number}"
    if part_number:
        return str(part_number)
    return f"item_{idx + 1}"


def compute_bom_id(bom: BillOfMaterials, source_document: str | None = None) -> str:
    payload = {
        "source_document": source_document,
        "items": [item.model_dump() for item in bom.items],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def apply_bom_update(base: BillOfMaterials, update: BOMUpdate) -> BillOfMaterials:
    override_map = {o.item_id: o for o in update.overrides}

    items = []
    for idx, item in enumerate(base.items):
        item_key = _bom_item_key(item, idx)
        override = override_map.get(item_key)
        if override is None:
            items.append(item)
            continue

        new_item = item.model_copy(deep=True)
        # Apply overrides
        new_item.quantity = override.quantity
        if override.item_nr is not None:
             new_item.item_nr = override.item_nr
        if override.xentral_number is not None:
             new_item.xentral_number = override.xentral_number
        if override.description is not None:
            new_item.description = override.description
        if override.unit is not None:
             new_item.unit = override.unit
        
        # Backward compatibility for component -> description
        if override.component is not None and override.description is None:
            new_item.description = override.component

        items.append(new_item)

    return BillOfMaterials(items=items)


def build_bom_tool_block(
    bom: BillOfMaterials,
    source_document: str | None = None,
    preview_image: str | None = None,
    *,
    bom_id: str | None = None,
    thread_id: str | None = None,
) -> ToolUseBlock:
    # Transform local temp path to served URL path
    if source_document:
        if os.path.isabs(source_document):
            temp_dir = tempfile.gettempdir()
            if source_document.startswith(temp_dir):
                filename = os.path.basename(source_document)
                source_document = f"/files/{filename}"
        elif not source_document.startswith("http") and not source_document.startswith("/files/"):
            # Assume it's a raw filename
            filename = os.path.basename(source_document)
            source_document = f"/files/{filename}"

    if preview_image:
        if os.path.isabs(preview_image):
            temp_dir = tempfile.gettempdir()
            if preview_image.startswith(temp_dir):
                filename = os.path.basename(preview_image)
                preview_image = f"/files/{filename}"
        elif not preview_image.startswith("http") and not preview_image.startswith("/files/"):
            filename = os.path.basename(preview_image)
            preview_image = f"/files/{filename}"

    rows: list[BOMRow] = []
    for idx, item in enumerate(bom.items):
        row_id = _bom_item_key(item, idx)
        
        # Mapping logic
        pos = item.part_number # "Pos" from drawing usually lands here
        item_nr = item.item_nr
        description = item.description or ""
        unit = item.unit or "Stk" # Default only if missing
        xentral_nr = item.xentral_number
        
        # "Component" is a legacy field for the UI, usually same as description or combined
        component_display = description if description else f"Item {idx+1}"

        rows.append(
            BOMRow(
                id=row_id,
                pos=pos,
                item_nr=item_nr,
                xentral_number=xentral_nr,
                component=component_display, # Kept for safety
                description=description,
                quantity=float(item.quantity) if item.quantity is not None else 0.0,
                unit=unit,
                confidence_score=None,
            )
        )

    bom_data = BOMTableData(
        rows=rows, 
        title=bom.title,
        source_document=source_document,
        preview_image=preview_image
    )
    data = bom_data.model_dump()
    if bom_id is None:
        bom_id = compute_bom_id(bom, source_document=source_document)
    data["bom_id"] = bom_id
    if thread_id is not None:
        data["thread_id"] = thread_id
    return ToolUseBlock(tool_name="display_bom_table", data=data)


def _parse_json_payload(payload: object) -> dict | None:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None
    return None


def _select_best_price(prices: list[dict]) -> dict | None:
    if not prices:
        return None
    priced = [p for p in prices if p.get("convertedPrice") is not None or p.get("price") is not None]
    if not priced:
        return None
    return min(
        priced,
        key=lambda p: p.get("convertedPrice")
        if p.get("convertedPrice") is not None
        else p.get("price", float("inf")),
    )


def _build_procurement_items_from_sup_multi_match(data: dict) -> list[dict]:
    items: list[dict] = []
    for match in data.get("supMultiMatch", []) or []:
        for part in match.get("parts", []) or []:
            component_name = (
                part.get("shortDescription")
                or part.get("name")
                or part.get("mpn")
                or "Unknown component"
            )
            options: list[dict] = []
            for seller in part.get("sellers", []) or []:
                company = seller.get("company", {}) or {}
                supplier_name = company.get("name") or "Unknown supplier"
                for offer in seller.get("offers", []) or []:
                    price_entry = _select_best_price(offer.get("prices", []) or [])
                    if not price_entry:
                        continue
                    price_per_unit = price_entry.get("convertedPrice", price_entry.get("price"))
                    if price_per_unit is None:
                        continue
                    options.append(
                        {
                            "supplier": supplier_name,
                            "part_number": offer.get("sku") or part.get("mpn") or "",
                            "price_per_unit": float(price_per_unit),
                            "currency": price_entry.get("convertedCurrency")
                            or price_entry.get("currency")
                            or "EUR",
                            "min_order_quantity": int(
                                offer.get("moq")
                                or price_entry.get("quantity")
                                or 1
                            ),
                            "delivery_time_days": int(offer.get("factoryLeadDays") or 0),
                            "in_stock": bool((offer.get("inventoryLevel") or 0) > 0),
                            "link": offer.get("clickUrl")
                            or company.get("homepageUrl")
                            or "",
                        }
                    )
            if options:
                items.append({"component_name": component_name, "options": options})
    return items


def _build_procurement_items_from_optimized(data: dict) -> list[dict]:
    items: list[dict] = []
    for part in data.get("parts", []) or []:
        seller = part.get("seller", {}) or {}
        component_name = part.get("selected_mpn") or part.get("original_mpn") or "Unknown component"
        unit_price = part.get("unit_price")
        if unit_price is None:
            continue
        options = [
            {
                "supplier": seller.get("name") or "Unknown supplier",
                "part_number": seller.get("sku") or part.get("selected_mpn") or "",
                "price_per_unit": float(unit_price),
                "currency": part.get("currency") or "EUR",
                "min_order_quantity": int(seller.get("moq") or 1),
                "delivery_time_days": int(seller.get("lead_time_days") or 0),
                "in_stock": bool((seller.get("inventory_level") or 0) > 0),
                "link": "",
            }
        ]
        items.append({"component_name": component_name, "options": options})
    return items


def _extract_procurement_items(payload: object) -> list[dict] | None:
    data = _parse_json_payload(payload)
    if not data or data.get("error"):
        return None

    if data.get("supMultiMatch"):
        return _build_procurement_items_from_sup_multi_match(data)
    if data.get("parts") and data.get("summary"):
        return _build_procurement_items_from_optimized(data)
    return None


def build_procurement_tool_block(payload: object) -> ToolUseBlock | None:
    items = _extract_procurement_items(payload)
    if not items:
        return None

    return ToolUseBlock(
        tool_name="display_procurement_options",
        data={"items_to_procure": items},
    )


def build_cost_analysis_tool_block(payload: object) -> ToolUseBlock | None:
    items = _extract_procurement_items(payload)
    if not items:
        return None

    cost_items: list[dict] = []
    total_cost = 0.0
    for item in items:
        options = item.get("options") or []
        if not options:
            continue
        best_option = min(options, key=lambda opt: opt.get("price_per_unit", float("inf")))
        amount = best_option.get("price_per_unit")
        if amount is None:
            continue
        min_order_quantity = best_option.get("min_order_quantity") or 1
        amount = float(amount) * float(min_order_quantity)
        total_cost += amount
        cost_items.append({"category": item.get("component_name") or "Unknown", "amount": amount})

    if not cost_items:
        return None

    return ToolUseBlock(
        tool_name="display_cost_analysis",
        data={"total_cost": total_cost, "items": cost_items},
    )


def append_to_history(history: dspy.History, user_query: str, process_result: str) -> None:
    history.messages.append({"user_query": user_query, "process_result": process_result})
    # Keep a bounded window to avoid unbounded prompt growth.
    max_turns = 25
    if len(history.messages) > max_turns:
        history.messages = history.messages[-max_turns:]


def extract_tool_calls_from_trajectory(trajectory: object) -> list[tuple[str, dict, object]]:
    """Extract ordered (tool_name, tool_args, observation) tuples from a ReAct trajectory."""
    if not isinstance(trajectory, dict):
        return []

    indices: list[int] = []
    for key in trajectory.keys():
        if isinstance(key, str) and key.startswith("tool_name_"):
            try:
                indices.append(int(key.split("_")[-1]))
            except ValueError:
                continue

    calls: list[tuple[str, dict, object]] = []
    for i in sorted(set(indices)):
        tool_name = trajectory.get(f"tool_name_{i}")
        tool_args = trajectory.get(f"tool_args_{i}", {}) or {}
        observation = trajectory.get(f"observation_{i}")
        if isinstance(tool_name, str) and isinstance(tool_args, dict):
            calls.append((tool_name, tool_args, observation))
    return calls
