from __future__ import annotations

import hashlib
import json

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
        new_item.quantity = int(override.quantity)
        if override.component is not None:
            new_item.description_of_part = override.component
        items.append(new_item)

    return BillOfMaterials(items=items)


def build_bom_tool_block(
    bom: BillOfMaterials,
    source_document: str | None = None,
    *,
    bom_id: str | None = None,
    thread_id: str | None = None,
) -> ToolUseBlock:
    rows: list[BOMRow] = []
    for idx, item in enumerate(bom.items):
        row_id = _bom_item_key(item, idx)
        component = item.description or f"Part {item.part_number}"
        description_bits = []
        if item.unit:
            description_bits.append(item.unit)
        #if item.no_of_poles:
        #    description_bits.append(f"{item.no_of_poles} poles")
        #if item.hdm_no:
        #    description_bits.append(f"HDM {item.hdm_no}")
        description = " | ".join(description_bits) if description_bits else None

        rows.append(
            BOMRow(
                id=row_id,
                component=component,
                quantity=item.quantity,
                unit="Stk",
                description=description,
                confidence_score=None,
            )
        )

    bom_data = BOMTableData(rows=rows, source_document=source_document)
    data = bom_data.model_dump()
    if bom_id is None:
        bom_id = compute_bom_id(bom, source_document=source_document)
    data["bom_id"] = bom_id
    if thread_id is not None:
        data["thread_id"] = thread_id
    return ToolUseBlock(tool_name="display_bom_table", data=data)


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
