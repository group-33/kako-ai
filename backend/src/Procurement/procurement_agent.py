import dspy
import json
from typing import List, Dict
from .nexarSupplyClient import NexarClient
from ..config import (
    NEXAR_CLIENT_ID,
    NEXAR_CLIENT_SECRET,
    GEMINI_API_KEY,
    PROCUREMENT_LLM_MODEL,
)
from query_manager import DEFAULT_QUERY, MULTI_QUERY_FULL


#### Signatures for Procurement Agent ####
class ToolSelectorSignature(dspy.Signature):
    """Given components to procure, select the right tools and arguments."""

    components: str = dspy.InputField(desc="JSON list of parts to order")
    preferences: str = dspy.InputField(desc="User preferences (cost, speed, etc.)")
    tools: List[dspy.Tool] = dspy.InputField()
    outputs: dspy.ToolCalls = dspy.OutputField()


class RecommendationSignature(dspy.Signature):
    """Synthesize API results into procurement recommendations."""

    components: str = dspy.InputField()
    api_results: str = dspy.InputField(desc="Results from Nexar API")
    preferences: str = dspy.InputField()
    recommendation: str = dspy.OutputField(desc="Final recommendation with reasoning")


#### Procurement Agent ####
class ProcurementAgent:
    def __init__(self):
        self.api_client = NexarClient(NEXAR_CLIENT_ID, NEXAR_CLIENT_SECRET)
        self.lm = dspy.LLM(model=PROCUREMENT_LLM_MODEL, api_key=GEMINI_API_KEY)
        dspy.settings.configure(lm=self.lm)

        self.tools = self._create_tools()

        self.select_tool = dspy.Predict(ToolSelectorSignature)
        self.synthesize = dspy.ChainOfThought(RecommendationSignature)

    #### Create Tools ####
    def _create_tools(self) -> List[dspy.Tool]:
        """Define the tools available to the agent."""

        tools = [
            dspy.Tool(
                name="search_part_by_mpn",
                description="Search for parts by their Manufacturer Part Numbers (MPNs).",
                func=self._tool_search_part_by_mpn,
                # signature=, TODO define signature
            ),
            dspy.Tool(
                name="find_alternatives",
                description="Find alternative to a part defined by its MPN based on the parts description.",
                func=self._tool_find_alternatives,
                # signature=, TODO define signature
            ),
            dspy.Tool(
                name="optimize_order",
                description="Optimize the order of parts based on TODO.",
                func=self._tool_optimize_order,
                # signature=, TODO define signature
            ),
        ]
        return tools

    #### Tool implementations ####
    def _tool_search_part_by_mpn(self, mpns: List[str], quantity: int = 1) -> str:
        """
        Searches for multiple parts by their MPNs.
        
        Args:
            mpns: A list of strings, where each string is a Manufacturer Part Number.
        """
        if not mpns or not isinstance(mpns, list):
            return json.dumps({"error": "Input must be a non-empty list of MPN strings."})
        variables = {"queries": [{"mpnOrSku": mpn, "limit": 1, "start": 0} for mpn in mpns]}
        # TODO handling of quantity etc.
        try:
            data = self.api_client.get_query(MULTI_QUERY_FULL, variables)
            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _tool_find_alternatives(
        self, mpn: str, description: str, quantity: int = 1
    ) -> str:
        # TODO implement alternative finding
        return json.dumps({"message": "find_alternatives not yet implemented"})

    def _tool_optimize_order(self, parts_json: str) -> str:
        # TODO implement order optimization
        return json.dumps({"message": "optimize_order not yet implemented"})

    #### Main agent call ####
    def __call__(self, components: List[Dict], preferences: Dict) -> str:
        """
        Main entry point.

        Args:
            components: [{"part_number": "STM32F407", "quantity": 100, "description": "MCU"}, ...]
            preferences: {"max_lead_time_days": 14, "prioritize": "cost"}

        Returns:
            Natural language procurement recommendation
        """
        print(f"[Agent] Processing {len(components)} components")

        components_str = json.dumps(components)
        preferences_str = json.dumps(preferences)

        response = self.select_tool(
            components=components_str, preferences=preferences_str, tools=self.tools
        )
        tool_calls = response.outputs.tool_calls

        all_results = []
        for call in tool_calls:
            result = call.execute(functions=self.tools)
            all_results.append(result)

        api_data = "\n".join(all_results)
        final = self.synthesize(
            components=components_str, api_results=api_data, preferences=preferences_str
        )

        return final.recommendation
