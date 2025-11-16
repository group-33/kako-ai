"""
Router-driven Demand Analyst agent powered by DSPy.

The agent first routes a user's request to the appropriate "tool"
inside the Xentral client and then optionally performs a deeper
LLM-backed feasibility analysis when needed.
"""
from __future__ import annotations

import json
from typing import Any, Optional, Dict

import dspy

from ..models import (
    BillOfMaterials,
    BOMItem,
    ToolCall,
    DemandAnalysisRequest,
    DemandAnalysisResponse,
    LackingMaterial,
)
from .xentral_client import XentralClient


class DemandAnalysisSignature(dspy.Signature):
    """Signature describing the feasibility analysis reasoning task."""

    user_query = dspy.InputField(
        desc="Original user request, e.g., 'Can we build 500 units?'"
    )
    quantity_required = dspy.InputField(
        desc="Number of units the user needs."
    )
    bom_json = dspy.InputField(
        desc="Bill of Materials for one unit encoded as JSON."
    )
    inventory_data = dspy.InputField(
        desc="JSON string describing stock levels for BOM parts."
    )
    pending_procurement = dspy.InputField(
        desc="JSON string of open procurement orders."
    )
    existing_orders = dspy.InputField(
        desc="JSON string of existing customer orders competing for stock."
    )

    analysis_report: DemandAnalysisResponse = dspy.OutputField(
        desc="Structured feasibility analysis."
    )


class DemandAnalysisRouterSignature(dspy.Signature):
    """Signature for routing user requests to the best available tool."""

    user_query = dspy.InputField(desc="The natural language request from the user.")
    available_tools = dspy.InputField(
        desc="JSON array describing the tools the agent can call."
    )

    chosen_tool: ToolCall = dspy.OutputField(
        desc="Structured tool call including parameters."
    )


class DemandAnalystAgent(dspy.Module):
    """Multi-tool DSPy agent for the Demand Analyst role."""

    def __init__(self) -> None:
        super().__init__()
        self.xentral_client = XentralClient()
        self.router_predictor = dspy.ChainOfThought(DemandAnalysisRouterSignature)
        self.analysis_predictor = dspy.ChainOfThought(DemandAnalysisSignature)

    def forward(
        self,
        request: Optional[DemandAnalysisRequest] = None,
        *,
        user_query: Optional[str] = None,
        bom: Optional[BillOfMaterials] = None,
        quantity_required: int = 1,
    ) -> Any:
        """
        Routes the user's request and executes the corresponding tool.

        The method accepts either a prepared DemandAnalysisRequest model or
        raw keyword arguments for convenience.
        """
        if request is None:
            if not user_query:
                raise ValueError("Either 'request' or 'user_query' must be provided.")
            request = DemandAnalysisRequest(
                bom=bom,
                user_query=user_query,
                quantity_required=quantity_required,
            )

        tools_json = json.dumps(self.xentral_client.available_tools, indent=2)
        print(f"--- 🧠 Routing demand query: '{request.user_query}' ---")

        try:
            route = self.router_predictor(
                user_query=request.user_query,
                available_tools=tools_json,
            )
            tool_call = route.chosen_tool
            print(f"--- 🤖 Selected tool: {tool_call.tool_name} ---")
        except Exception as exc:
            print(f"ERROR while routing request: {exc}")
            return {"error": "Demand Analyst could not understand the request."}

        return self._execute_tool(tool_call, request)

    # --- Internal helpers -------------------------------------------------
    def _execute_tool(
        self,
        tool_call: ToolCall,
        request: DemandAnalysisRequest,
    ) -> Any:
        """Executes the selected tool and handles special cases."""
        tool_args: Dict[str, Any] = dict(tool_call.tool_input or {})

        if tool_call.tool_name == "run_full_feasibility_analysis":
            if not request.bom:
                return {"error": "This request requires a BOM, but none was provided."}
            tool_args.setdefault("quantity_required", request.quantity_required)
            tool_args["bom"] = request.bom

            try:
                context = self.xentral_client.run_full_feasibility_analysis(**tool_args)
            except Exception as exc:
                print(f"ERROR fetching feasibility context: {exc}")
                return {"error": "Failed to fetch inventory context from Xentral."}

            return self._run_feasibility_analysis(request, context)

        try:
            method = getattr(self.xentral_client, tool_call.tool_name)
        except AttributeError:
            return {"error": f"Tool '{tool_call.tool_name}' is not implemented."}

        try:
            return method(**tool_args)
        except TypeError as exc:
            print(f"ERROR calling tool '{tool_call.tool_name}': {exc}")
            return {
                "error": (
                    f"Tool '{tool_call.tool_name}' received unexpected arguments."
                )
            }
        except Exception as exc:
            print(f"ERROR during tool execution: {exc}")
            return {"error": f"An unexpected error occurred: {exc}"}

    def _run_feasibility_analysis(
        self,
        request: DemandAnalysisRequest,
        context: Dict[str, Any],
    ) -> DemandAnalysisResponse:
        """Runs the Chain-of-Thought module to produce structured analysis."""
        assert request.bom is not None, "BOM is required at this stage."

        bom_json = request.bom.model_dump_json()
        inventory_json = json.dumps(context.get("inventory", {}))
        pending_json = json.dumps(context.get("pending_procurement", []), default=str)
        existing_json = json.dumps(context.get("existing_orders", []), default=str)

        try:
            result = self.analysis_predictor(
                user_query=request.user_query,
                quantity_required=str(request.quantity_required),
                bom_json=bom_json,
                inventory_data=inventory_json,
                pending_procurement=pending_json,
                existing_orders=existing_json,
            )
            return result.analysis_report
        except Exception as exc:
            print(f"ERROR in feasibility analysis: {exc}")
            return DemandAnalysisResponse(
                status="unavailable",
                analysis_summary=f"Error during analysis: {exc}",
                lacking_materials=[],
            )


# --- Local smoke test -----------------------------------------------------
def test_demand_analyst_router() -> None:
    """Runs two mock scenarios to exercise the router pipeline."""
    print("--- 1. Configuring Mock LM ---")

    mock_tool_call_1 = ToolCall(
        tool_name="list_deliveries_in_range",
        tool_input={"start_date": "2025-11-20", "end_date": "2025-11-30"},
    ).model_dump_json()

    mock_tool_call_2 = ToolCall(
        tool_name="run_full_feasibility_analysis",
        tool_input={"quantity_required": 500},
    ).model_dump_json()

    mock_analysis_response = DemandAnalysisResponse(
        status="partial",
        analysis_summary=(
            "20 units of PN-123 are available, but 500 are required. "
            "All other parts are sufficiently stocked."
        ),
        lacking_materials=[
            LackingMaterial(
                part_number="PN-123",
                quantity_needed=500,
                quantity_in_stock=20,
            )
        ],
    ).model_dump_json()

    lm = dspy.MockLM([mock_tool_call_1, mock_tool_call_2, mock_analysis_response])
    dspy.settings.configure(lm=lm)

    print("--- 2. Initializing DemandAnalystAgent ---")
    demand_agent = DemandAnalystAgent()

    print("--- 3. Run Test 1 (List Deliveries) ---")
    req1 = DemandAnalysisRequest(
        bom=None,
        user_query="Show me all deliveries arriving next week (2025-11-20 to 2025-11-30).",
    )
    result1 = demand_agent(request=req1)
    print("\n--- ✅ Test 1 Result ---")
    print(json.dumps(result1, indent=2))

    print("\n--- 4. Run Test 2 (Full Feasibility) ---")
    mock_bom = BillOfMaterials(
        items=[
            BOMItem(
                part_number="PN-123",
                quantity=1,
                description_of_part="Main connector",
                no_of_poles=8,
                order_number=1001,
                hdm_no=700,
                measurments_in_discription="10cm",
            )
        ]
    )
    req2 = DemandAnalysisRequest(
        bom=mock_bom,
        user_query="Can we build 500 units of the new cable assembly?",
        quantity_required=500,
    )
    result2 = demand_agent(request=req2)
    print("\n--- ✅ Test 2 Result ---")
    if isinstance(result2, DemandAnalysisResponse):
        print(result2.model_dump_json(indent=2))
    else:
        print(json.dumps(result2, indent=2))


if __name__ == "__main__":
    test_demand_analyst_router()
