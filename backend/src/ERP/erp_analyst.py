#QUERY: Zeige mir alle Stücklisten für die nächsten Zeiteinheit
#Use dspy to process question
#create tools to get products from sales_orders and parts from products

import dspy
import requests
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
from typing import ClassVar, Dict, Any, List

BASE_URL = os.getenv("BASE_URL")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#lm = dspy.LM("gemini/gemini-2.0-flash", api_key=GEMINI_API_KEY)
#dspy.settings.configure(lm=lm)

class ToolSelectorSignature(dspy.Signature):
    """Given a user question, select the right tool(s) and arguments to answer it."""
    __doc__ = __doc__.strip()
    question: str = dspy.InputField()
    tools: List[dspy.Tool] = dspy.InputField()
    outputs: dspy.ToolCalls = dspy.OutputField()

class AnswerSignature(dspy.Signature):
    """Given the user's question and JSON data from an API, provide a helpful, natural language answer in German."""
    __doc__ = __doc__.strip()
    question = dspy.InputField()
    api_data = dspy.InputField(desc="The JSON string result(s) from the tool(s).")
    answer = dspy.OutputField(desc="The final, natural language answer.")

# --- 2. The Agent Class ---
# This class wraps all logic and state.

class XentralAgent:
    def __init__(self):
        # --- 1. Environment & Config ---
        self.base_url = os.getenv("BASE_URL")
        self.api_token = os.getenv("BEARER_TOKEN")
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not all([self.base_url, self.api_token, gemini_api_key]):
            raise ValueError("Missing one or more env variables: BASE_URL, BEARER_TOKEN, GEMINI_API_KEY")

        # --- 2. Configure LM ---
        # We use dspy.Google, not the generic dspy.LM
        self.lm = dspy.LM(model="gemini/gemini-2.0-flash", api_key=gemini_api_key)
        dspy.settings.configure(lm=self.lm)
        
        # --- 3. Build Headers ---
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # --- 4. Define & Wrap Tools ---
        # We wrap our *internal* method `_get_sales_orders_by_date`
        orders_tool = dspy.Tool(
            func=self._tool_get_sales_orders,
            name="get_sales_orders",
            desc="Gets a list of sales orders (Aufträge) for a future time window. Returns order details."
        )

        boms_tool = dspy.Tool(
            func=self._tool_get_future_boms,
            name="get_future_boms",
            desc="Gets a list of Bill of Materials (Stücklisten) required for orders in a future time window."
        )

        self.tools = [orders_tool, boms_tool]

        # --- 5. DSPy Modules ---
        # This module *selects* the tool
        self.select_tool = dspy.Predict(ToolSelectorSignature)
        # This module *uses* the tool's output to answer
        self.synthesize_answer = dspy.ChainOfThought(AnswerSignature)

    def _calculate_dates(self, time_quantity: str, time_unit: str):
        """Helper to calculate start and end dates based on inputs."""
        try:
            today_obj = datetime.now().astimezone()
            # Floor to midnight
            today_obj = today_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            
            quantity = int(time_quantity)
            unit = time_unit.lower()
            end_date_obj = None

            if unit in ['tag', 'tage', 'day', 'days']:
                end_date_obj = today_obj + timedelta(days=quantity)
            elif unit in ['woche', 'wochen', 'week', 'weeks']:
                end_date_obj = today_obj + timedelta(weeks=quantity)
            elif unit in ['monat', 'monate', 'month', 'months']:
                end_date_obj = today_obj + relativedelta(months=quantity)
            else:
                raise ValueError(f"Invalid time unit: {time_unit}")

            # Format to ISO without seconds/microseconds for Xentral
            # e.g. 2025-11-19T00:00+01:00
            from_date = today_obj.isoformat(timespec='minutes')
            to_date = end_date_obj.isoformat(timespec='minutes')
            
            return from_date, to_date
        except Exception as e:
            return None, str(e)
        
    def _fetch_orders(self, from_date: str, to_date: str) -> List[Dict]:
        """Helper to execute the specific API call for orders."""
        url = self.base_url + "/api/v1/belege/auftraege"
        
        params = {
            "filter[0][property]": "tatsaechlichesLieferdatum",
            "filter[0][expression]": "gte",
            "filter[0][value]": from_date,
            "filter[1][property]": "tatsaechlichesLieferdatum",
            "filter[1][expression]": "lte",
            "filter[1][value]": to_date,
            "include": "positionen", # Critical: We need positions to find products
            "items": 1000
        }

        print(f"[API Call] GET Sales Orders: {from_date} to {to_date}")
        res = requests.get(url, params=params, headers=self.headers, timeout=10)
        print(res.status_code)
        print(res.request.url)
        res.raise_for_status()
        if not res.content:
            return []
        
        data = res.json()
        print(len(data))
        # Handle different Xentral response structures (list vs dict with 'data' key)
        if isinstance(data, dict) and 'data' in data:
            return data['data']
        elif isinstance(data, list):
            return data
        return []

    def _fetch_bom_for_product(self, product_id: str) -> List[Dict]:
        """
        Helper to fetch BOM (Stückliste) for a specific product ID.
        NOTE: You may need to adjust the URL based on your specific Xentral version.
        """
        # Try standard endpoint for a specific article's BOM
        # Alternative URL structure might be: /api/v1/stuecklisten?produkt={id}
        url = self.base_url + f"/api/v1/products/{product_id}/parts"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=5)
            if res.status_code == 200 and res.content:
                 data = res.json()
                 if isinstance(data, dict) and 'data' in data:
                     return data['data']
                 return data
            return []
        except Exception as e:
            print(f"[API Error] Failed to get BOM for product {product_id}: {e}")
            return []

    def _tool_get_sales_orders(self, time_quantity: str, time_unit: str) -> str:
        """Tool 1: Just get the orders."""
        from_date, to_date = self._calculate_dates(time_quantity, time_unit)
        if not from_date:
            return json.dumps({"error": to_date}) # to_date holds error msg here

        try:
            orders = self._fetch_orders(from_date, to_date)
            return json.dumps(orders)
        except Exception as e:
            return json.dumps({"error": str(e)})
        
    
    def _tool_get_future_boms(self, time_quantity: str, time_unit: str) -> str:
        """
        Tool 2: The Smart Orchestrator.
        1. Gets Orders
        2. Extracts Products
        3. Gets BOMs for those Products
        4. Returns aggregated list
        """
        #print("here in get future boms")
        print(f"[Tool: get_future_boms] Started for {time_quantity} {time_unit}")
        
        # 1. Get Orders
        from_date, to_date = self._calculate_dates(time_quantity, time_unit)
        if not from_date:
            return json.dumps({"error": to_date})

        try:
            orders = self._fetch_orders(from_date, to_date)
        except Exception as e:
            return json.dumps({"error": f"Failed to fetch orders: {e}"})

        if not orders:
            return json.dumps({"message": "No orders found in this timeframe."})
        
        print(orders)

        # 2. Extract Unique Product IDs from Positions
        product_map = {} # ID -> Name mapping for clarity
        
        for order in orders:
            # 'positionen' might be a list or a dict depending on API version
            positions = order.get('positionen', [])
            if not positions:
                continue
                
            for pos in positions:
                # Xentral fields vary. Look for 'artikel', 'produkt', 'artikel_id'
                # Adjust these keys based on your specific API response
                p_id = pos.get('artikel') or pos.get('produkt') or pos.get('artikel_id')
                p_name = pos.get('artikel_bezeichnung') or pos.get('bezeichnung')
                
                if p_id:
                    product_map[str(p_id)] = p_name

        print(f"[Logic] Found {len(product_map)} unique products in {len(orders)} orders.")
        
        # 3. Fetch BOMs for each unique product
        # We loop here so the LLM doesn't have to.
        results = []
        
        for p_id, p_name in product_map.items():
            boms = self._fetch_bom_for_product(p_id)
            
            if boms:
                results.append({
                    "parent_product_id": p_id,
                    "parent_product_name": p_name,
                    "bom_components": boms
                })
            else:
                # It might be a simple product with no BOM
                pass

        if not results:
            return json.dumps({"message": "Orders found, but no associated Bill of Materials (Stücklisten) could be retrieved. The products might be simple articles without sub-components."})

        return json.dumps({
            "summary": f"Found {len(results)} products with BOMs for orders between {from_date} and {to_date}",
            "details": results
        })


    def __call__(self, question: str) -> str:
        print(f"User Question: {question}\n")
        
        print("--- Step 1: Selecting Tool ---")
        response = self.select_tool(question=question, tools=self.tools)
        tool_calls = response.outputs.tool_calls
        print(f"Tool Plan: {tool_calls}")

        print("\n--- Step 2: Executing Tool ---")
        all_results = []
        if not tool_calls:
            all_results.append(json.dumps({"error": "No tool was selected."}))
        else:
            for call in tool_calls:
                print(f"Calling: {call.name} with args {call.args}")
                # We pass self.tools so execute() can find the function
                result_str = call.execute(functions=self.tools)
                print(f"Got Result length: {len(result_str)} chars")
                all_results.append(result_str)

        print("\n--- Step 3: Synthesizing Answer ---")
        api_data_str = "\n".join(all_results)
        # Truncate if result is massive to avoid Context Window overflow
        if len(api_data_str) > 30000: 
            api_data_str = api_data_str[:30000] + "... [truncated]"
            
        final_response = self.synthesize_answer(question=question, api_data=api_data_str)
        
        print(f"Final Answer: {final_response.answer}")
        return final_response.answer
