from __future__ import annotations

import json

import dspy

from backend.src.models import BillOfMaterials, DemandAnalysisResponse
from backend.src.demand_analysis.tools import run_full_feasibility_analysis


class FeasibilityCheck(dspy.Signature):
    """Determine if the requested quantity can be built given the BOM and current context."""

    user_query = dspy.InputField(
        desc="User's feasibility question, e.g., 'Can we build 500 units?'"
    )
    quantity_required = dspy.InputField(
        desc="Units requested for the build."
    )
    bom_json = dspy.InputField(
        desc="BOM for one unit encoded as JSON."
    )
    inventory_data = dspy.InputField(
        desc="JSON string describing current stock levels for BOM parts."
    )
    pending_procurement = dspy.InputField(
        desc="JSON string of open procurement orders for BOM parts."
    )
    existing_orders = dspy.InputField(
        desc="JSON string of existing customer orders competing for stock."
    )

    analysis_report: DemandAnalysisResponse = dspy.OutputField(
        desc="Structured feasibility analysis with status and any lacking materials."
    )


def run_structured_feasibility_check(
    user_request: str,
    bom: BillOfMaterials,
    quantity_required: int = 1,
) -> DemandAnalysisResponse:
    """Run full feasibility check: fetch context, then produce a structured DemandAnalysisResponse."""
    context = run_full_feasibility_analysis(bom=bom, quantity_required=quantity_required)

    bom_json = bom.model_dump_json()
    inventory_json = json.dumps(context.get("inventory", {}))
    pending_json = json.dumps(context.get("pending_procurement", []), default=str)
    existing_json = json.dumps(context.get("existing_orders", []), default=str)

    feasibility_predictor = dspy.ChainOfThought(FeasibilityCheck)
    result = feasibility_predictor(
        user_query=user_request,
        quantity_required=str(quantity_required),
        bom_json=bom_json,
        inventory_data=inventory_json,
        pending_procurement=pending_json,
        existing_orders=existing_json,
    )
    return result.analysis_report
