# Coinbase Advanced Trade API Python Client

This is the unofficial Python client for the Coinbase Advanced Trade API. It allows users to interact with the API to manage their cryptocurrency trading activities on the Coinbase platform.

## Features

- Easy-to-use Python wrapper for the Coinbase Advanced Trade API
- Supports all endpoints and methods provided by the official API
- Lightweight and efficient implementation

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

## Usage

Here's an example of how to use the package: 

```python
 from coinbase_advanced_trader import coinbase_client
 from coinbase_advanced_trader.coinbase_client import Side

 # Set your API key and secret
 API_KEY = "your_api_key"
 API_SECRET = "your_api_secret"

 # Set the credentials
 coinbase_client.set_credentials(API_KEY, API_SECRET)


 def buy_bitcoin(amount, currency="USD", price=None):
     product_id = f"BTC-{currency}"

     if price:
         order_type = "limit_limit_gtc"
         order_configuration = {
             order_type: {
                 "base_size": str(amount),
                 "limit_price": str(price)
             }
         }
     else:
         order_type = "market_market_ioc"
         order_configuration = {
             order_type: {
                 "quote_size": str(amount),
             }
         }

     client_order_id = coinbase_client.generate_client_order_id()
     side = Side.BUY.name

     response = coinbase_client.createOrder(
         client_order_id=client_order_id,
         product_id=product_id,
         side=side,
         order_configuration=order_configuration
     )

     return response


 amount_to_buy = 0.001
 currency = "USD"

 # You can specify a price for a limit order, or leave it as None for a market order
 price = 10000

 response = buy_bitcoin(amount_to_buy, currency, price)
 print("Buy order response:", response)
```

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

