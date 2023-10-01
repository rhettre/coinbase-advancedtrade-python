# Coinbase Advanced Trade API Python Client

This is the unofficial Python client for the Coinbase Advanced Trade API. It allows users to interact with the API to manage their cryptocurrency trading activities on the Coinbase platform.

## Features

- Easy-to-use Python wrapper for the Coinbase Advanced Trade API
- Supports all endpoints and methods provided by the official API
- Lightweight and efficient wrapper
- Added support for trading strategies covered on the [YouTube channel](https://rhett.blog/youtube)

## Setup

   1. Clone this repository or download the source files by running
         ```bash
            pip install coinbase-advancedtrade-python

   2. Set your API key and secret in config.py. To obtain your API key and secret, follow the steps below:
      - Log in to your Coinbase account.
      - Navigate to API settings.
      - Create a new API key with the appropriate permissions.
      - Copy the API key and secret to config.py.

## Authentication
Here's an example of how to authenticate: 

````python
from coinbase_advanced_trader.config import set_api_credentials

# Set your API key and secret
API_KEY = "ABCD1234"
API_SECRET = "XYZ9876"

# Set the API credentials once, and it updates the CBAuth singleton instance
set_api_credentials(API_KEY, API_SECRET)
````

## Usage of Strategies

Here's an example of how to use the strategies package to buy $20 worth of Bitcoin: 

````python
from coinbase_advanced_trader.strategies.limit_order_strategies import fiat_limit_buy

# Define the trading parameters
product_id = "BTC-USD"  # Replace with your desired trading pair
usd_size = 20  # Replace with your desired USD amount to spend``

# Perform a limit buy
limit_buy_order = fiat_limit_buy(product_id, usd_size)
````

## Usage of Fear and Greed Index
````python
from coinbase_advanced_trader.strategies.fear_and_greed_strategies import trade_based_on_fgi_simple

# Define the product id
product_id = "BTC-USD"

# Implement the strategy
trade_based_on_fgi_simple(product_id, 10)

````

## Usage of Fear and Greed Index (Pro)
````python
from coinbase_advanced_trader.strategies.fear_and_greed_strategies import trade_based_on_fgi_pro

# Define the product id
product_id = "BTC-USD"

# Define the custom schedule
custom_schedule = [
    {"threshold": 20, "factor": 1, "action": "buy"},
    {"threshold": 80, "factor": 0.5, "action": "buy"},
    {"threshold": 100, "factor": 1, "action": "sell"},
]

# Implement the strategy
response = trade_based_on_fgi_pro(product_id, 10, custom_schedule)
````

## Documentation

For more information about the Coinbase Advanced Trader API, consult the [official API documentation](https://docs.cloud.coinbase.com/advanced-trade-api/docs/rest-api-overview/).

## License
    This project is licensed under the MIT License. See the LICENSE file for more information.

## Author
    Rhett Reisman

    Email: rhett@rhett.blog

    GitHub: https://github.com/rhettre/coinbase-advancedtrade-python

## Disclaimer

This project is not affiliated with, maintained, or endorsed by Coinbase. Use this software at your own risk. Trading cryptocurrencies carries a risk of financial loss. The developers of this software are not responsible for any financial losses or damages incurred while using this software. Nothing in this software should be seen as an inducement to trade with a particular strategy or as financial advice.

