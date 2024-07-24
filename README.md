# Coinbase Advanced Trade API Python Client

This is the unofficial Python client for the Coinbase Advanced Trade API. It allows users to interact with the API to manage their cryptocurrency trading activities on the Coinbase platform.

## Features

- Easy-to-use Python wrapper for the Coinbase Advanced Trade API
- Supports the new Coinbase Cloud authentication method
- Built on top of the official [Coinbase Python SDK](https://github.com/coinbase/coinbase-advanced-py) for improved stability
- Supports all endpoints and methods provided by the official API
- Added support for trading strategies covered on the [YouTube channel](https://rhett.blog/youtube)

## Setup

1. Install the package using pip:
   ```bash
   pip install coinbase-advancedtrade-python
   ```

2. Obtain your API key and secret from the Coinbase Developer Platform. The new API key format looks like this:
   ```
   API Key: organizations/{org_id}/apiKeys/{key_id}
   API Secret: -----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n
   ```

## Authentication

Here's an example of how to authenticate using the new method:

```python
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient

api_key = "organizations/{org_id}/apiKeys/{key_id}"
api_secret = "-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n"

client = EnhancedRESTClient(api_key=api_key, api_secret=api_secret)
```

## Using the Official SDK

The `EnhancedRESTClient` inherits from the Coinbase SDK's `RESTClient`, which means you can use all the functions provided by the official SDK. Here's an example of how to use the `get_product` function:

```python
product_info = client.get_product(product_id="BTC-USDC")

print(product_info)
```

## Using Wrapper Strategies

Here's an example of how to use the strategies package to buy $10 worth of Bitcoin. By making assumptions about limit price in [trading_config.py](coinbase_advanced_trader/trading_config.py) we are able to simplify the syntax for making orders:

```python
# Perform a market buy
client.fiat_market_buy("BTC-USDC", "10")

#Place a $10 buy order for BTC-USD near the current spot price of BTC-USDC
client.fiat_limit_buy("BTC-USDC", "10")

#Place a $10 buy order for BTC-USD at a limit price of $10,000
client.fiat_limit_buy("BTC-USDC", "10", "10000")

#Place a $10 buy order for BTC-USD at a 10% discount from the current spot price of BTC-USDC
client.fiat_limit_buy("BTC-USDC", "10", price_multiplier=".90")

#Place a $10 sell order for BTC-USD at a limit price of $100,000
client.fiat_limit_sell("BTC-USDC", "10", "100000")

#Place a $10 sell order for BTC-USD near the current spot price of BTC-USDC
client.fiat_limit_sell("BTC-USDC", "5")

#Place a $10 sell order for BTC-USD at a 10% premium to the current spot price of BTC-USDC
client.fiat_limit_sell("BTC-USDC", "5", price_multiplier="1.1")
```

### Account Balance Operations

The `EnhancedRESTClient` provides methods to retrieve account balances for cryptocurrencies. These methods are particularly useful for managing and monitoring your cryptocurrency holdings on Coinbase.

#### Listing All Non-Zero Crypto Balances

To get a dictionary of all cryptocurrencies with non-zero balances in your account:

```python
balances = client.list_held_crypto_balances()
print(balances)
```

#### Getting a Specific Crypto Balance

To get the available balance of a specific cryptocurrency in your account (returns 0 if the specified cryptocurrency is not found in the account):

```python
balance = client.get_crypto_balance("BTC")
print(balance)
```

Note: Both methods use a caching mechanism to reduce API calls. The account data is cached for one hour before a fresh fetch is made from Coinbase.

### Usage of Fear and Greed Index

```python
# Trade based on Fear and Greed Index
client.trade_based_on_fgi("BTC-USDC", "10")
```

You can also update and retrieve the Fear and Greed Index schedule:

```python
# Get current FGI schedule
current_schedule = client.get_fgi_schedule()

# Update FGI schedule
new_schedule = [
    {'threshold': 15, 'factor': 1.2, 'action': 'buy'},
    {'threshold': 37, 'factor': 1.0, 'action': 'buy'},
    {'threshold': 35, 'factor': 0.8, 'action': 'sell'},
    {'threshold': 45, 'factor': 0.6, 'action': 'sell'}
]
client.update_fgi_schedule(new_schedule)
```

## Legacy Support

The legacy authentication method is still supported but moved to a separate module. It will not receive the latest updates from the Coinbase SDK. To use the legacy method:

```python
from coinbase_advanced_trader.legacy.legacy_config import set_api_credentials
from coinbase_advanced_trader.legacy.strategies.limit_order_strategies import fiat_limit_buy

legacy_key = "your_legacy_key"
legacy_secret = "your_legacy_secret"

set_api_credentials(legacy_key, legacy_secret)

# Use legacy functions
limit_buy_order = fiat_limit_buy("BTC-USDC", 10)
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

This project is not affiliated with, maintained, or endorsed by Coinbase. Use this software at your own risk. Trading cryptocurrencies carries a risk of financial loss. The developers of this software are not responsible for any financial losses or damages incurred while using this software. Nothing in this software should be seen as an inducement to trade with a particular strategy or as financial advice.