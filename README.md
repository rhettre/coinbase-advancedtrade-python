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

2. For development, install test dependencies:
   ```bash
   pip install -e ".[test]"
   ```

3. Run tests:
   ```bash
   python -m unittest discover -s coinbase_advanced_trader/tests
   ```

2. Obtain your API key and secret from the Coinbase Developer Platform. The new API key format looks like:
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

To get the available balance of a specific cryptocurrency in your account, use `get_crypto_balance`. It leverages the enhanced caching mechanism for efficient data retrieval and returns a Decimal balance (0 if no account is found):

```python
balance = client.get_crypto_balance("BTC")
print(balance)
```

Note: Both methods use a caching mechanism to reduce API calls. The account data is cached for one hour before a fresh fetch is made from Coinbase.

#### Enhanced Account Information
In addition to retrieving basic balances, the `EnhancedRESTClient` supports fetching detailed account information via the `get_account_by_currency` method. This method:
  - Uses cached account data to quickly locate the account by currency.
  - Makes an additional API call with the account's UUID to retrieve further details such as:
      - Account Name
      - Account Type
      - Active Status
      - Account Creation Date

**When to Use This:**  
Use `get_account_by_currency` if you need comprehensive details for a specific account—for example, when you need to verify account information prior to initiating deposits or withdrawals.

**Example:**
```python
# Get detailed account info for the USD account
account = client.get_account_by_currency("USD")
if account:
    print(f"Account UUID: {account.uuid}")
    print(f"Account Name: {account.name}")
    print(f"Balance: {account.available_balance} {account.currency}")
else:
    print("No account found for USD")
```
### Fiat Deposit Example

You can deposit fiat (for example, USD) into your Coinbase account using the deposit functionality. The example below shows how to deposit $25 USD using known account and payment method IDs. (In real use, replace the placeholder IDs with your actual values.)

**Example:**

```python
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient

# Initialize your client (ensure your API key and secret are set securely)
client = EnhancedRESTClient(api_key="your_api_key", api_secret="your_api_secret")

# Show available deposit methods run this before depositing to get the ID of your payment method (bank account, etc)
client.show_deposit_methods() 

# Deposit $25 USD into your Coinbase account using known IDs
client.deposit_fiat(
    account_id="your_usd_account_id",         # Replace with your actual USD account ID (see get_account_by_currency)
    payment_method_id="your_payment_method_id", # Replace with your actual payment method ID (see show_deposit_methods)
    amount="25.00",
    currency="USD"
)
```

All deposit details are logged automatically by the service. Be sure to use secure methods for storing and retrieving your keys and account identifiers.


### Usage of Fear and Greed Index

The client uses the [fear-and-greed-crypto](https://github.com/rhettre/fear-and-greed-crypto) package to fetch the current Fear and Greed Index value. This index helps determine market sentiment and automate trading decisions.

```python
# Trade based on Fear and Greed Index
client.trade_based_on_fgi("BTC-USDC", "10")
```

You can customize the trading behavior by updating the Fear and Greed Index schedule:

```python
# Get current FGI schedule
current_schedule = client.get_fgi_schedule()

# Update FGI schedule with custom thresholds and actions
new_schedule = [
    {'threshold': 15, 'factor': 1.2, 'action': 'buy'},   # Buy more in extreme fear
    {'threshold': 37, 'factor': 1.0, 'action': 'buy'},   # Buy normal amount in fear
    {'threshold': 35, 'factor': 0.8, 'action': 'sell'},  # Sell some in greed
    {'threshold': 45, 'factor': 0.6, 'action': 'sell'}   # Sell more in extreme greed
]
client.update_fgi_schedule(new_schedule)
```

The schedule determines:
- When to buy or sell based on the Fear and Greed Index value
- How much to adjust the trade amount (using the factor)
- What action to take at each threshold

For example, with the above schedule:
- If FGI is 10 (Extreme Fear), it will buy with 1.2x the specified amount
- If FGI is 50 (Neutral), no trade will be executed
- If FGI is 80 (Extreme Greed), it will sell with 0.6x the specified amount

## AlphaSquared Integration

This client now includes integration with AlphaSquared, allowing you to execute trading strategies based on AlphaSquared's risk analysis.

### Setup

1. Obtain your AlphaSquared API key from [AlphaSquared](https://alphasquared.io/).

2. Initialize the AlphaSquared client along with the Coinbase client:

```python
from coinbase_advanced_trader import EnhancedRESTClient, AlphaSquaredTrader
from alphasquared import AlphaSquared

# Initialize Coinbase client
coinbase_api_key = "YOUR_COINBASE_API_KEY"

coinbase_api_secret = "YOUR_COINBASE_API_SECRET"

coinbase_client = EnhancedRESTClient(api_key=coinbase_api_key, api_secret=coinbase_api_secret)

# Initialize AlphaSquared client
alphasquared_api_key = "YOUR_ALPHASQUARED_API_KEY"

alphasquared_client = AlphaSquared(alphasquared_api_key, cache_ttl=60)

# Create AlphaSquaredTrader
trader = AlphaSquaredTrader(coinbase_client, alphasquared_client)
```

### Executing AlphaSquared Strategies

To execute a trading strategy based on AlphaSquared's risk analysis:

```python
# Set trading parameters
product_id = "BTC-USDC"

# Your custom strategy name from AlphaSquared
strategy_name = "My Custom Strategy"

# Execute strategy
trader.execute_strategy(product_id, strategy_name)
```

This will:
1. Fetch the current risk level for the specified asset from AlphaSquared.
2. Determine the appropriate action (buy/sell) and value based on the custom strategy defined in AlphaSquared and the current risk.
3. Execute the appropriate trade on Coinbase if the conditions are met.

> **Note:** Make sure to handle exceptions and implement proper logging in your production code. This integration only works with custom strategies; it does not work with the default strategies provided by AlphaSquared.

### Customizing Strategies

You can create custom strategies by modifying the `execute_strategy` method in the `AlphaSquaredTrader` class. This allows you to define specific trading logic based on the risk levels provided by AlphaSquared.

## AWS Lambda Compatibility

When using this package in AWS Lambda, ensure your Lambda function is configured to use Python 3.12. The cryptography binaries in the Lambda layer are compiled for Python 3.12, and using a different Python runtime version will result in compatibility issues.

To configure your Lambda function:
1. Set the runtime to Python 3.12
2. Use the provided Lambda layer from the latest release
3. If building custom layers, ensure they are built using the same Python version as the Lambda runtime.

## Documentation

For more information about the Coinbase Advanced Trader API, consult the [official API documentation](https://docs.cdp.coinbase.com/advanced-trade/docs/welcome).

## License

This project is licensed under the MIT License. See the LICENSE file for more information.

## Author

Rhett Reisman

Email: rhett@rhett.blog

GitHub: https://github.com/rhettre/coinbase-advancedtrade-python

## Disclaimer

This project is not affiliated with, maintained, or endorsed by Coinbase. Use this software at your own risk. Trading cryptocurrencies carries a risk of financial loss. The developers of this software are not responsible for any financial losses or damages incurred while using this software. Nothing in this software should be seen as an inducement to trade with a particular strategy or as financial advice.

