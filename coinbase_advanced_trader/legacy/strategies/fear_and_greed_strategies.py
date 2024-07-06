import requests
from coinbase_advanced_trader.legacy.strategies.limit_order_strategies import fiat_limit_buy, fiat_limit_sell
from ..legacy_config import SIMPLE_SCHEDULE, PRO_SCHEDULE


def get_fear_and_greed_index():
    """
    Fetches the latest Fear and Greed Index (FGI) values from the API.

    Returns:
        tuple: A tuple containing the FGI value and its classification.
    """
    response = requests.get('https://api.alternative.me/fng/?limit=1')
    data = response.json()['data'][0]
    return int(data['value']), data['value_classification']


def trade_based_on_fgi_simple(product_id, fiat_amount, schedule=SIMPLE_SCHEDULE):
    """
    Executes a trade based on the Fear and Greed Index (FGI) using a simple strategy.

    Args:
        product_id (str): The ID of the product to trade.
        fiat_amount (float): The amount of fiat currency to trade.
        schedule (list, optional): The trading schedule. Defaults to SIMPLE_SCHEDULE.

    Returns:
        dict: The response from the trade execution.
    """

    fgi, classification = get_fear_and_greed_index()

    # Use the provided schedule or the default one
    schedule = schedule or SIMPLE_SCHEDULE

    # Sort the schedule by threshold in ascending order
    schedule.sort(key=lambda x: x['threshold'])

    # Get the lower and higher threshold values
    lower_threshold = schedule[0]['threshold']
    higher_threshold = schedule[-1]['threshold']

    for condition in schedule:
        if fgi <= condition['threshold']:
            fiat_amount *= condition['factor']
            if condition['action'] == 'buy':
                return fiat_limit_buy(product_id, fiat_amount)
        elif lower_threshold < fgi < higher_threshold:
            response = fiat_limit_buy(product_id, fiat_amount)
        else:
            response = fiat_limit_sell(product_id, fiat_amount)
        return {**response, 'Fear and Greed Index': fgi, 'classification': classification}


def trade_based_on_fgi_pro(product_id, fiat_amount, schedule=PRO_SCHEDULE):
    """
    Executes a trade based on the Fear and Greed Index (FGI) using a professional strategy.

    Args:
        product_id (str): The ID of the product to trade.
        fiat_amount (float): The amount of fiat currency to trade.
        schedule (list, optional): The trading schedule. Defaults to PRO_SCHEDULE.

    Returns:
        dict: The response from the trade execution.
    """

    fgi, classification = get_fear_and_greed_index()

    # Use the provided schedule or the default one
    schedule = schedule or PRO_SCHEDULE

    for condition in schedule:
        if fgi <= condition['threshold']:
            fiat_amount *= condition['factor']
            if condition['action'] == 'buy':
                response = fiat_limit_buy(product_id, fiat_amount)
            else:
                response = fiat_limit_sell(product_id, fiat_amount)
            return {**response, 'Fear and Greed Index': fgi, 'classification': classification}
