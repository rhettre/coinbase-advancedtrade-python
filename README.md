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

   2. Install the required Python packages:
         ```bash
            pip install -r requirements.txt

   3. Set your API key and secret in config.py. To obtain your API key and secret, follow the steps below:
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
usd_size = 20  # Replace with your desired USD amount to spend

# Perform a limit buy for just below the spot price of your desired trading pair
limit_buy_order = fiat_limit_buy(product_id, usd_size)
print("Limit Sell Order Response:", limit_buy_order)

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

This project is not affiliated with, maintained, or endorsed by Coinbase. Use this software at your own risk. Trading cryptocurrencies carries a risk of financial loss. The developers of this software are not responsible for any financial losses or damages incurred while using this software.

