import json
from typing import List, Dict, Optional
from .nexarSupplyClient import NexarClient
from ..config import (
    NEXAR_CLIENT_ID,
    NEXAR_CLIENT_SECRET,
    PROCUREMENT_API_IS_LIVE,
)
from .query_manager import MULTI_QUERY_FULL, SEARCH_BY_CATEGORY_QUERY


# Initialize shared client
_nexar_client = NexarClient(
    NEXAR_CLIENT_ID, NEXAR_CLIENT_SECRET, is_live=PROCUREMENT_API_IS_LIVE
)


def search_part_by_mpn(mpns: List[str], quantity: int = 1) -> str:
    """
    Search for electronic parts by their Manufacturer Part Numbers (MPNs).
    Returns detailed part information including pricing, availability, and seller options.

    Use this when you need to look up specific parts by MPN to check pricing and availability.
    The quantity parameter helps understand which price breaks apply.

    Args:
        mpns: List of Manufacturer Part Numbers to search (e.g., ["STM32F407VGT6", "LM324N"])
        quantity: Quantity needed per part (default: 1)

    Returns:
        JSON string containing part details, specifications, pricing tiers, availability,
        and seller information from the Nexar supply API

    Example:
        search_part_by_mpn(["STM32F407VGT6"], quantity=100)
    """
    if not mpns or not isinstance(mpns, list):
        return json.dumps({"error": "Input must be a non-empty list of MPN strings."})

    # Limit to 3 results per MPN to conserve API quota
    variables = {"queries": [{"mpnOrSku": mpn, "limit": 1, "start": 0} for mpn in mpns]}

    try:
        data = _nexar_client.get_query(MULTI_QUERY_FULL, variables)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": str(e)})


def find_alternatives(mpn: str, description: str, quantity: int = 1) -> str:
    """
    Find alternative electronic parts that are compatible with the specified MPN.
    Searches for parts with similar specifications in the same category.

    Use this when the original part is unavailable, too expensive, or has insufficient stock.
    The alternatives returned will have the same category and similar specs for compatibility.

    Args:
        mpn: Original Manufacturer Part Number to find alternatives for
        description: Part description to help match similar components
        quantity: Quantity needed (default: 1)

    Returns:
        JSON string with original part info and up to 3 alternative parts with full specs,
        pricing, and availability data for compatibility comparison

    Example:
        find_alternatives("STM32F407VGT6", "32-bit MCU 168MHz", quantity=100)
    """
    # First, get the original part to extract category and specs
    try:
        original_search = search_part_by_mpn([mpn], quantity=quantity)
        original_data = json.loads(original_search)

        if "error" in original_data:
            return json.dumps(
                {
                    "error": f"Could not find original part {mpn}",
                    "original_search": original_data,
                }
            )

        # Extract original part data
        parts = original_data.get("supMultiMatch", [])
        if not parts or not parts[0].get("parts"):
            return json.dumps(
                {"error": f"No data found for MPN {mpn}", "alternatives": []}
            )

        original_part = parts[0]["parts"][0]
        # category_id = original_part.get("category", {}).get("id", "")

        # Search for alternatives using description and category
        variables = {"description": description}  # , "categoryId": category_id

        alternatives_data = _nexar_client.get_query(SEARCH_BY_CATEGORY_QUERY, variables)

        # Combine original and alternatives for comparison
        result = {
            "original_mpn": mpn,
            "original_part": original_part,
            "alternatives": alternatives_data.get("supSearch", {}).get("results", []),
            "note": "Compare specs carefully to ensure exact compatibility",
        }

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": str(e)})


def optimize_order(parts_list: List[Dict]) -> str:
    """
    Optimize procurement for an entire Bill of Materials (BOM). Searches all parts,
    finds alternatives for unavailable items, and selects the lowest-cost valid option
    for each part considering quantity requirements and MOQ constraints.

    Use this for complete BOM procurement planning. It handles the full pipeline:
    searching parts, checking availability against required quantities, finding alternatives
    when needed, and selecting the best offer from available sellers.

    Args:
        parts_list: List of parts to procure, each with 'mpn' and 'quantity' keys
                   Example: [{"mpn": "STM32F407VGT6", "quantity": 100}, {"mpn": "LM324N", "quantity": 50}]

    Returns:
        JSON string with optimized procurement plan including selected MPN, pricing,
        seller details, and alternatives used. Includes summary with total cost estimate.

    Example:
        optimize_order([{"mpn": "STM32F407VGT6", "quantity": 100}, {"mpn": "LM324N", "quantity": 50}])
    """
    if not parts_list or not isinstance(parts_list, list):
        return json.dumps({"error": "Input must be a non-empty list of parts"})

    # Extract MPNs and create quantity lookup
    mpns = [part.get("mpn") for part in parts_list if part.get("mpn")]
    quantity_map = {part["mpn"]: part["quantity"] for part in parts_list}

    # Batch search all parts
    search_results_json = search_part_by_mpn(mpns)
    search_data = json.loads(search_results_json)

    if "error" in search_data:
        return json.dumps({"error": "Failed to search parts", "details": search_data})

    result = {
        "summary": {
            "total_parts": len(parts_list),
            "found_directly": 0,
            "alternatives_used": 0,
            "total_estimated_cost": 0.0,
            "currency": "USD",
        },
        "parts": [],
        "warnings": [],
    }

    # Process each part from the search results
    for match_result in search_data.get("supMultiMatch", []):
        parts = match_result.get("parts", [])
        if not parts:
            continue

        part_data = parts[0]
        original_mpn = part_data.get("mpn")
        quantity_needed = quantity_map.get(original_mpn, 1)

        # Try to select best offer from original part
        selected = _select_best_offer(part_data, quantity_needed)

        if selected:
            result["summary"]["found_directly"] += 1
            result["parts"].append(selected)
        else:
            # Need to find alternative
            result["warnings"].append(
                f"Part {original_mpn}: Insufficient stock or no valid offers, searching alternatives"
            )

            alternative_json = find_alternatives(
                mpn=original_mpn,
                description=part_data.get("shortDescription", ""),
                quantity=quantity_needed,
            )
            alternative_data = json.loads(alternative_json)

            # Try to select from alternatives
            alt_selected = _select_best_alternative(
                alternative_data, quantity_needed, original_mpn
            )

            if alt_selected:
                result["summary"]["alternatives_used"] += 1
                result["parts"].append(alt_selected)
            else:
                result["warnings"].append(
                    f"Part {original_mpn}: No suitable alternatives found with sufficient stock"
                )

    # Calculate total cost
    result["summary"]["total_estimated_cost"] = sum(
        part.get("total_price", 0) for part in result["parts"]
    )

    return json.dumps(result, indent=2)


def _select_best_offer(part_data: Dict, quantity_needed: int) -> Optional[Dict]:
    """
    Select the best (lowest cost) offer from a part's sellers that meets quantity requirements.

    Args:
        part_data: Part data from Nexar API
        quantity_needed: Required quantity

    Returns:
        Dict with selected offer details, or None if no valid offers
    """
    mpn = part_data.get("mpn")
    best_offer = None
    best_price_per_unit = float("inf")

    for seller in part_data.get("sellers", []):
        for offer in seller.get("offers", []):
            inventory = offer.get("inventoryLevel", 0)
            moq = offer.get("moq", 1)

            # Check if this offer can fulfill our needs
            if inventory < quantity_needed:
                continue

            # Calculate quantity to order (round up to MOQ if needed)
            order_quantity = max(quantity_needed, moq)

            # Find applicable price tier
            prices = offer.get("prices", [])
            applicable_price = _find_applicable_price(prices, order_quantity)

            if applicable_price is None:
                continue

            unit_price = applicable_price.get("convertedPrice", 0)

            if unit_price < best_price_per_unit:
                best_price_per_unit = unit_price
                best_offer = {
                    "original_mpn": mpn,
                    "selected_mpn": mpn,
                    "quantity_requested": quantity_needed,
                    "quantity_ordered": order_quantity,
                    "manufacturer": part_data.get("manufacturer", {}).get(
                        "name", "Unknown"
                    ),
                    "unit_price": unit_price,
                    "total_price": unit_price * order_quantity,
                    "currency": applicable_price.get("convertedCurrency", "USD"),
                    "seller": {
                        "name": seller.get("company", {}).get("name", "Unknown"),
                        "sku": offer.get("sku", ""),
                        "inventory_level": inventory,
                        "moq": moq,
                        "lead_time_days": offer.get("factoryLeadDays", 0),
                    },
                    "alternative_reason": None,
                }

    return best_offer


def _select_best_alternative(
    alternative_data: Dict, quantity_needed: int, original_mpn: str
) -> Optional[Dict]:
    """
    Select the best alternative from search results.

    Args:
        alternative_data: Alternative search results from find_alternatives
        quantity_needed: Required quantity
        original_mpn: Original part number for reference

    Returns:
        Dict with selected alternative details, or None if no valid alternatives
    """
    if "error" in alternative_data:
        return None

    alternatives = alternative_data.get("alternatives", [])

    for result in alternatives:
        part = result.get("part", {})

        # Skip if it's the same MPN as original
        if part.get("mpn") == original_mpn:
            continue

        # Try to select best offer from this alternative
        selected = _select_best_offer(part, quantity_needed)

        if selected:
            # Mark as alternative
            selected["original_mpn"] = original_mpn
            selected["alternative_reason"] = (
                "Original part unavailable, selected compatible alternative"
            )
            return selected

    return None


def _find_applicable_price(prices: List[Dict], quantity: int) -> Optional[Dict]:
    """
    Find the applicable price tier for a given quantity.

    Args:
        prices: List of price tiers
        quantity: Order quantity

    Returns:
        Price dict for the applicable tier, or None if not found
    """
    if not prices:
        return None

    # Sort by quantity ascending
    sorted_prices = sorted(prices, key=lambda p: p.get("quantity", 0))

    # Find the highest tier that doesn't exceed our quantity
    applicable = None
    for price in sorted_prices:
        if price.get("quantity", 0) <= quantity:
            applicable = price
        else:
            break

    return applicable if applicable else sorted_prices[0]
