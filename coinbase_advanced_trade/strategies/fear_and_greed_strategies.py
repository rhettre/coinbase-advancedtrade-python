import requests
from coinbase_advanced_trade.CBAClient import CBAClient
from coinbase_advanced_trade.product import Product
from typing import Any, Optional

# Default schedule for the trade_based_on_fgi_simple function
SIMPLE_SCHEDULE: list[dict[str, int | float | str]] = [
    {"threshold": 20, "factor": 1.2, "action": "buy"},
    {"threshold": 80, "factor": 0.8, "action": "sell"},
]

# Default schedule for the trade_based_on_fgi_pro function
PRO_SCHEDULE: list[dict[str, int | float | str]] = [
    {"threshold": 10, "factor": 1.5, "action": "buy"},
    {"threshold": 20, "factor": 1.3, "action": "buy"},
    {"threshold": 30, "factor": 1.1, "action": "buy"},
    {"threshold": 70, "factor": 0.9, "action": "sell"},
    {"threshold": 80, "factor": 0.7, "action": "sell"},
    {"threshold": 90, "factor": 0.5, "action": "sell"},
]


def get_fear_and_greed_index() -> tuple[int, str]:
    """
    Fetches the latest Fear and Greed Index (FGI) values from the API.

    Returns:
        tuple: A tuple containing the FGI value and its classification.
    """
    response = requests.get("https://api.alternative.me/fng/?limit=1")
    data = response.json()["data"][0]
    return int(data["value"]), str(data["value_classification"])


def trade_based_on_fgi_simple(product_id:str, fiat_amount:float, schedule:list[dict[str, int | float | str]]=SIMPLE_SCHEDULE,client:Optional[CBAClient]=None) -> dict[str, Any | int | str] | None:
    """
    Executes a trade based on the Fear and Greed Index (FGI) using a simple strategy.

    Args:
        product_id (str): The ID of the product to trade.
        fiat_amount (float): The amount of fiat currency to trade.
        schedule (list, optional): The trading schedule. Defaults to SIMPLE_SCHEDULE.

    Returns:
        dict: The response from the trade execution.
    """
    if client is None:
        client = CBAClient()
    fgi:int
    classification:str
    fgi, classification = get_fear_and_greed_index()
    # Sort the schedule by threshold in ascending order
    schedule.sort(key=lambda x: x["threshold"])

    # Get the lower and higher threshold values
    lower_threshold: float = float(schedule[0]["threshold"])
    higher_threshold: float = float(schedule[-1]["threshold"])
    product:Product = client.getProduct(product_id)
    
    for condition in schedule:
        if fgi <= float(condition["threshold"]):
            fiat_amount *= float(condition["factor"])
            if condition["action"] == "buy":
                response:dict[str,Any] = client.buy(product, fiat_amount)
            else:
                response:dict[str,Any] = {}# this should probably be something else but I don't know what
        elif lower_threshold < fgi < higher_threshold:
            response:dict[str,Any] = client.buy(product, fiat_amount)
        else:
            response:dict[str,Any] = client.sell(product, fiat_amount)
        return {
            **response,
            "Fear and Greed Index": fgi,
            "classification": classification,
        }


def trade_based_on_fgi_pro(product_id:str, fiat_amount:float, schedule:list[dict[str, int | float | str]]=PRO_SCHEDULE,client:Optional[CBAClient]=None) -> dict[str, int | str] | None:
    """
    Executes a trade based on the Fear and Greed Index (FGI) using a professional strategy.

    Args:
        product_id (str): The ID of the product to trade.
        fiat_amount (float): The amount of fiat currency to trade.
        schedule (list, optional): The trading schedule. Defaults to PRO_SCHEDULE.

    Returns:
        dict: The response from the trade execution.
    """
    if client is None:
        client = CBAClient()
    fgi:int
    classification:str
    fgi, classification = get_fear_and_greed_index()
    product:Product = client.getProduct(product_id)
    # Use the provided schedule or the default one
    schedule = schedule or PRO_SCHEDULE

    for condition in schedule:
        if fgi <= float(condition["threshold"]):
            fiat_amount *= float(condition["factor"])
            if condition["action"] == "buy":
                response = client.buy(product, fiat_amount)
            else:
                response = client.sell(product, fiat_amount)
            return {
                **response,
                "Fear and Greed Index": fgi,
                "classification": classification,
            }
