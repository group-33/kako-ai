"""Unified KakoAI ReAct agent wiring available tools."""

from __future__ import annotations

import dspy

from backend.src.tools.bom_extraction.bom_tool import perform_bom_extraction
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
)
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
    process_result: str = dspy.OutputField(
        desc="Natural-language summary of the reasoning steps and tool results."
    )


TOOLBOX = [
    perform_bom_extraction,
    run_full_feasibility_analysis,
    list_deliveries_in_range,
    get_inventory_for_part,
    get_inventory_for_bom,
    get_pending_procurement_orders,
    get_existing_customer_orders,
    get_sales_orders,
    get_future_boms,
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
        self.agent = dspy.ReAct(KakoAgentSignature, tools=TOOLBOX)

    def __call__(self, user_query: str) -> dspy.Prediction:
        """Invoke the agent with a natural-language request and return the ReAct prediction."""
        return self.agent(user_query=user_query)
