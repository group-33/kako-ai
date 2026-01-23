"""Unified KakoAI ReAct agent wiring available tools."""

from __future__ import annotations

import dspy

from backend.src.tools.bom_extraction.bom_tool import (
    perform_bom_extraction,
    perform_bom_extraction_upload,
)
from backend.src.tools.demand_analysis.feasibility import (
    run_structured_feasibility_check,
)
from backend.src.tools.demand_analysis.inventory import (
    run_full_feasibility_analysis,
    list_deliveries_in_range,
    get_inventory_for_part,
    get_inventory_for_bom,
    get_pending_procurement_orders,
    get_existing_customer_orders,
    get_sales_orders,
    get_future_boms,
    get_orders_by_customer,
    get_boms_for_orders,
)
from backend.src.tools.demand_analysis.bom import bom_check, perform_bom_matching
from backend.src.tools.procurement.procurement import (
    filter_sellers_by_shipping,
    sort_and_filter_by_best_price,
    search_part_by_mpn,
    find_alternatives,
    optimize_order,
)


class KakoAgentSignature(dspy.Signature):
    """You are KakoAI: solve the user's request by reasoning and calling tools when useful."""

    user_query: str = dspy.InputField(
        desc="Natural-language task or question to solve; include any specifics such as file paths or part numbers."
    )
    history: dspy.History = dspy.InputField(
        desc="Conversation history for this thread; use it to maintain context across turns."
    )
    process_result: str = dspy.OutputField(
        desc="Natural-language summary. REQUIRED: If you extracted a BOM, just say 'I have extracted the BOM information.' Do NOT list the items in the text response."
    )


TOOLBOX = [
    perform_bom_extraction,
    perform_bom_extraction_upload,
    # Demand analysis
    bom_check,
    perform_bom_matching,
    run_full_feasibility_analysis,
    list_deliveries_in_range,
    get_inventory_for_part,
    get_inventory_for_bom,
    get_pending_procurement_orders,
    get_existing_customer_orders,
    get_sales_orders,
    get_future_boms,
    get_orders_by_customer,
    get_boms_for_orders,
    run_structured_feasibility_check,
    # procurement tools
    filter_sellers_by_shipping,
    sort_and_filter_by_best_price,
    search_part_by_mpn,
    find_alternatives,
    optimize_order,
]


class KakoAgent:
    """Thin wrapper around the unified ReAct agent."""

    def __init__(self) -> None:
        # Reduce max_iters to 2 (from default 5-7) to save API quota
        self.agent = dspy.ReAct(KakoAgentSignature, tools=TOOLBOX, max_iters=2)

    def __call__(
        self, user_query: str, history: dspy.History | None = None
    ) -> dspy.Prediction:
        """Invoke the agent with a natural-language request and return the ReAct prediction."""
        if history is None:
            history = dspy.History(messages=[])
        return self.agent(user_query=user_query, history=history)
