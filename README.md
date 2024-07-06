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

## Usage of Strategies

Here's an example of how to use the strategies package to buy $10 worth of Bitcoin:

```python
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient

client = EnhancedRESTClient(api_key=api_key, api_secret=api_secret)

# Perform a market buy
client.fiat_market_buy("BTC-USDC", "10")

# Perform a limit buy
client.fiat_limit_buy("BTC-USDC", "10")
```

## Usage of Fear and Greed Index

```python
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient

client = EnhancedRESTClient(api_key=api_key, api_secret=api_secret)

# Trade based on Fear and Greed Index
client.trade_based_on_fgi("BTC-USDC", "10")
```

## Advanced Usage

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