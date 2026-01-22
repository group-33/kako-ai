#QUERY: Zeige mir alle Stücklisten für die nächsten Zeiteinheit
#Use dspy to process question
#create tools to get products from sales_orders and parts from products

import dspy
import requests
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
from typing import ClassVar, Dict, Any 

BASE_URL = os.getenv("BASE_URL")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

lm = dspy.LM("gemini/gemini-2.0-flash", api_key=GEMINI_API_KEY)
dspy.settings.configure(lm=lm)

class SalesOrders_Retrieval_Signature(dspy.Signature):
    #Use this tool to get a list of all Stücklisten that are due within a time frame
    time_quantity = dspy.InputField(desc="The number of time units(e.g., for '6 Wochen'), this is a 6.")
    time_unit = dspy.InputField(desc="The time unit. Must be one of 'Tage', 'Wochen', 'Monate', or Jahre.")
    bom_list_json = dspy.OutputField(desc="The JSON response from the API (a list of BOMs) as a string.")


def retrieve_salesOrders(time_quantity: str, time_unit: str) -> str:
    """
    Use this tool to get a list of all Stücklisten that are due within a time frame.
    
    Args:
        time_quantity: The number of time units (e.g., for '6 Wochen', this is '6')
        time_unit: The time unit. Must be one of 'Tage', 'Wochen', or 'Monate'
    
    Returns:
        JSON response from the API (a list of sales orders with BOMs) as a string
    """
    if not BEARER_TOKEN:
        raise ValueError("BEARER_TOKEN environment variable is not set.")
    if not BASE_URL:
        raise ValueError("BASE_URL environment variable is not set.")
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    today = datetime.now()
    from_date = today.strftime('%Y-%m-%d')
        
    quantity = int(time_quantity)
        
    if time_unit == 'Tage':
        to_date = (today + timedelta(days=quantity)).strftime('%Y-%m-%d')
    elif time_unit == 'Wochen':
        to_date = (today + timedelta(weeks=quantity)).strftime('%Y-%m-%d')
    elif time_unit == 'Monate':
        to_date = (today + relativedelta(months=quantity)).strftime('%Y-%m-%d')
    else:
        return json.dumps({"error": f"Invalid time_unit: '{time_unit}'. Must be 'Tage', 'Wochen', or 'Monate'."})
    
    url = BASE_URL + "/api/v1/salesOrders"

    # Note: Date filtering appears to cause server errors in the Xentral API
    # So we retrieve all orders and include the date range in the response
    # The LLM will filter the results based on the dates
    params = {
        "page[number]": 1,
        "page[size]": 50  # Maximum allowed by API
    }
    
    response_text = requests.get(url, headers=headers, params=params).text
    
    # Add metadata about the requested date range to help the LLM filter
    response_data = json.loads(response_text)
    response_data["_metadata"] = {
        "requested_date_range": {
            "from": from_date,
            "to": to_date
        },
        "instruction": "Filter the sales orders to only include those with orderDate within the requested date range."
    }
    
    return json.dumps(response_data)

# Create the tool instance
SalesOrders_Retrieval_Tool = dspy.Tool(retrieve_salesOrders, 
                                       name="retrieve_salesOrders", 
                                       desc="Retrieve sales orders for a specified time frame")
    

class Xentral_Agent_Signature(dspy.Signature):
    """Answer questions about Xentral ERP data in German by using the available tools."""
    
    question = dspy.InputField(desc="A natural language question about Xentral data, in German.")
    answer = dspy.OutputField(desc="A clear, natural language answer in German, based on the API results.")
        