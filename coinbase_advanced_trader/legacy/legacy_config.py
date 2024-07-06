import os
from coinbase_advanced_trader.legacy.cb_auth import CBAuth

API_KEY = None
API_SECRET = None

# Default price multipliers for limit orders
BUY_PRICE_MULTIPLIER = 0.995
SELL_PRICE_MULTIPLIER = 1.005

# Default schedule for the trade_based_on_fgi_simple function
SIMPLE_SCHEDULE = [
    {'threshold': 20, 'factor': 1.2, 'action': 'buy'},
    {'threshold': 80, 'factor': 0.8, 'action': 'sell'}
]

# Default schedule for the trade_based_on_fgi_pro function
PRO_SCHEDULE = [
    {'threshold': 10, 'factor': 1.5, 'action': 'buy'},
    {'threshold': 20, 'factor': 1.3, 'action': 'buy'},
    {'threshold': 30, 'factor': 1.1, 'action': 'buy'},
    {'threshold': 70, 'factor': 0.9, 'action': 'sell'},
    {'threshold': 80, 'factor': 0.7, 'action': 'sell'},
    {'threshold': 90, 'factor': 0.5, 'action': 'sell'}
]


def set_api_credentials(api_key=None, api_secret=None):
    global API_KEY
    global API_SECRET

    # Option 1: Use provided arguments
    if api_key and api_secret:
        API_KEY = api_key
        API_SECRET = api_secret

    # Option 2: Use environment variables
    elif 'COINBASE_API_KEY' in os.environ and 'COINBASE_API_SECRET' in os.environ:
        API_KEY = os.environ['COINBASE_API_KEY']
        API_SECRET = os.environ['COINBASE_API_SECRET']

    # Option 3: Load from a separate file (e.g., keys.txt)
    else:
        try:
            with open('keys.txt', 'r') as f:
                API_KEY = f.readline().strip()
                API_SECRET = f.readline().strip()
        except FileNotFoundError:
            print("Error: API keys not found. Please set your API keys.")

    # Update the CBAuth singleton instance with the new credentials
    CBAuth().set_credentials(API_KEY, API_SECRET)
