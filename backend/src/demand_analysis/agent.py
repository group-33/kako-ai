from __future__ import annotations

import dspy

from backend.src.models import BillOfMaterials
from backend.src.demand_analysis import tools
from backend.src.demand_analysis.feasibility import run_structured_feasibility_check
from backend.src.config import GEMINI_2_5_PRO

class DemandAnalyst(dspy.Signature):
    """As a senior demand analyst for KAKO, use the available tools to complete the user's inventory/feasibility request."""

    user_request: str = dspy.InputField(
        desc="Natural language request to complete, e.g., 'Show deliveries next week' or 'Can we build 500 units?'."
    )
    bom: BillOfMaterials | None = dspy.InputField(
        desc="Bill of Materials for the product, when relevant.", default=None
    )
    quantity_required: int = dspy.InputField(
        desc="Number of units requested by the user.", default=1
    )

    process_result: str = dspy.OutputField(
        desc=(
            "Summary of the tool calls and results, including any key data such as "
            "lacking parts or fetched deliveries."
        )
    )


TOOLBOX = [
    tools.run_full_feasibility_analysis,
    tools.list_deliveries_in_range,
    tools.get_inventory_for_part,
    tools.get_sales_orders,
    tools.get_future_boms,
    run_structured_feasibility_check,
]


class DemandAnalystAgent:
    """Thin wrapper around a DSPy ReAct agent wired to demand-analysis tools."""

    def __init__(self) -> None:
        self.agent = dspy.ReAct(DemandAnalyst, tools=TOOLBOX)

    def __call__(self, user_request: str, bom: BillOfMaterials | None = None, quantity_required: int = 1) -> dspy.Prediction:
        """Invoke the agent with the given request and optional BOM context."""
        return self.agent(user_request=user_request, bom=bom, quantity_required=quantity_required)


if __name__ == '__main__':
    with dspy.context(lm=GEMINI_2_5_PRO):
        agent = DemandAnalystAgent()
        result = agent(user_request='Zeige mir alle Stücklisten für die nächsten 6 Wochen.')
        print(result.process_result)
