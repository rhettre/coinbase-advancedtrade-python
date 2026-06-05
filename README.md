# Coinbase Advanced Trade API Python Client

This is the unofficial Python client for the Coinbase Advanced Trade API. It allows users to interact with the API to manage their cryptocurrency trading activities on the Coinbase platform.

## Features

- Easy-to-use Python wrapper for the Coinbase Advanced Trade API
- Supports the new Coinbase Cloud authentication method
- Built on top of the official [Coinbase Python SDK](https://github.com/coinbase/coinbase-advanced-py) for improved stability
- Supports all endpoints and methods provided by the official API
- Adds beginner-friendly WebSocket workflows for live prices, user order events, and fill-driven automation
- Added support for trading strategies covered on the [YouTube channel](https://rhett.blog/youtube)

## Setup

This package supports Python 3.12 and newer, including Python 3.14.

1. Install the package using pip:
   ```bash
   pip install coinbase-advancedtrade-python
   ```

2. For development, install test dependencies:
   ```bash
   pip install -e .
   pip install -r test-requirements.txt
   ```

3. Run tests:
   ```bash
   python -m unittest discover -s coinbase_advanced_trader/tests
   ```

4. Obtain your API key and secret from the Coinbase Developer Platform. The new API key format looks like:
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

You can also use environment variables, which is the recommended pattern for long-running bots and cloud deployment:

```bash
export COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
export COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n"
```

```python
from coinbase_advanced_trader import EnhancedRESTClient

client = EnhancedRESTClient()
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

# Place a $10 buy order near the current spot price (allows taker by default)
client.fiat_limit_buy("BTC-USDC", "10")

# Force maker-only (post-only) buy for lower fees
client.fiat_limit_buy("BTC-USDC", "10", post_only=True)

# Place a $10 buy order at a specific limit price (allows taker by default)
client.fiat_limit_buy("BTC-USDC", "10", "10000")

# Force maker-only at a specific limit price
client.fiat_limit_buy("BTC-USDC", "10", "10000", post_only=True)

# Place a $10 buy order at a 10% discount (allows taker by default)
client.fiat_limit_buy("BTC-USDC", "10", price_multiplier=".90")

# Force maker-only with price multiplier
client.fiat_limit_buy("BTC-USDC", "10", price_multiplier=".90", post_only=True)

# Place a $10 sell order at a specific limit price (allows taker by default)
client.fiat_limit_sell("BTC-USDC", "10", "100000")

# Place a $10 sell order near the current spot price (allows taker by default)
client.fiat_limit_sell("BTC-USDC", "5")

# Force maker-only (post-only) sell for lower fees
client.fiat_limit_sell("BTC-USDC", "5", post_only=True)

# Place a $10 sell order at a 10% premium (allows taker by default)
client.fiat_limit_sell("BTC-USDC", "5", price_multiplier="1.1")

# Force maker-only with price multiplier
client.fiat_limit_sell("BTC-USDC", "5", price_multiplier="1.1", post_only=True)
```

### WebSocket Tutorial Helpers

REST asks Coinbase for the latest state. WebSockets let Coinbase push live events to your script. The official SDK already exposes all low-level channels, so this wrapper focuses on practical workflows.

The tutorial series is built around a conservative framing:

- Slow strategy logic can use REST candles and reference data.
- Live order handling should use the authenticated WebSocket user channel.
- No helper can guarantee daily or weekly profit; fees, slippage, volatility, and venue risk still matter.

#### Public Live Prices

This demo does not require an API key:

```python
from coinbase_advanced_trader import EnhancedRESTClient

client = EnhancedRESTClient()

client.watch_prices(["BTC-USDC", "ETH-USDC"], seconds=10)
```

Use a callback when you want to control the output:

```python
def print_price(update):
    print(f"{update.product_id}: {update.price}")

client.watch_ticker(
    ["BTC-USDC", "ETH-USDC"],
    seconds=10,
    callback=print_price,
    print_prices=False
)
```

#### Authenticated Order Events

The `user` channel reports live order updates such as open, filled, and cancelled events. This requires API keys with the right Coinbase permissions:

```python
from coinbase_advanced_trader import EnhancedRESTClient

client = EnhancedRESTClient()

def print_order_event(event):
    print(
        event.order_id,
        event.product_id,
        event.status,
        event.filled_size,
        event.average_filled_price
    )

client.watch_order_events(
    ["BTC-USDC"],
    callback=print_order_event,
    seconds=60
)
```

#### Wait for a Fill

This is the first wrapper-level WebSocket business case: place an order, then wait for Coinbase to push the fill event instead of polling REST in a loop.

```python
order = client.fiat_market_buy("BTC-USDC", "10")

fill = client.wait_for_order_fill(
    order_id=order.id,
    product_id="BTC-USDC",
    timeout=300
)

print(fill.filled_size, fill.average_filled_price)
```

#### Buy, Then Place a Take-Profit Sell

This helper places a fiat market buy, waits for the actual fill, then places a sell limit order using the filled base size and average fill price.
It opens the authenticated user WebSocket before sending the buy order, which helps avoid missing very fast market-order fill events.

```python
result = client.buy_then_limit_sell_on_fill(
    product_id="BTC-USDC",
    fiat_amount="10",
    sell_price_multiplier="1.05"
)

print(result["buy_order"].id)
print(result["fill"].average_filled_price)
print(result["sell_order"].id)
```

This is a take-profit automation, not guaranteed profit or spread capture. Fees, slippage, and price movement still matter.

#### Dry-Run Volatility-Targeted Trend Plan

For a more trader-focused demo, start with a plan that does not place orders. This helper reads public daily candles, checks the recent trend, estimates annualized volatility using 365-day crypto annualization, and returns a long-only target notional.

```python
from coinbase_advanced_trader import EnhancedRESTClient

client = EnhancedRESTClient()

plan = client.build_volatility_targeted_trend_plan(
    product_id="BTC-USDC",
    quote_budget="100",
    lookback_days=120,
    momentum_days=30,
    target_annual_volatility="0.08"
)

print(plan.as_dict())
```

This is a dry-run planning helper, not an execution signal by itself. A practical bot should still apply fee checks, account constraints, position limits, and explicit approval or additional execution logic before placing orders.

#### Safety Helper

For demos where you place far-away or post-only orders, you can clean up open orders:

```python
client.cancel_open_orders(product_id="BTC-USDC")
```

### Post-Only vs Allow Taker

By default, limit orders allow taker execution, meaning they may execute immediately against existing orders (incurring taker fees). To force maker-only execution and qualify for lower fees, pass `post_only=True`. Post-only orders add liquidity and will be rejected if they would immediately match.

**When to use post_only=True:**
- Lower fees via maker-only fills
- You prefer resting on the book vs immediate execution

**When to keep default (post_only=False):**
- You want immediate execution
- You accept higher taker fees for speed

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

For portfolio-specific daily demos, use the static-dollar ladder helper. BUY and SELL amounts are fixed quote-currency amounts, not percentages of the portfolio:

```python
result = client.trade_based_on_fgi_ladder(
    product_id="BTC-USDC",
    portfolio_uuid="YOUR_FEAR_AND_GREED_PORTFOLIO_UUID",
    base_amount="1.00"
)

print(result)
```

The default static ladder buys more during fear, holds through neutral and moderate greed, and sells a fixed $1.00 above the greed threshold.

## AlphaSquared Integration

This client includes integration with AlphaSquared. The recommended workflow is to poll pending AlphaSquared strategy actions, place the corresponding Coinbase order, and then mark the AlphaSquared action as executed only after Coinbase accepts the order.

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

### Executing Pending AlphaSquared Actions

To execute pending AlphaSquared strategy actions:

```python
# Set trading parameters
product_id = "BTC-USDC"

# Your custom strategy name from AlphaSquared
strategy_name = "My Custom Strategy"

# Poll pending actions, place Coinbase limit orders, then check off AlphaSquared
results = trader.execute_pending_strategy_actions(
    product_id,
    strategy_name=strategy_name
)

for result in results:
    print(result.as_dict())
```

This will:

1. Fetch pending AlphaSquared actions with `executed=False`.
2. Translate BUY actions into Coinbase limit buys where the AlphaSquared value is the quote currency amount to spend.
3. Translate SELL actions into Coinbase limit sells where the AlphaSquared value is the percentage of available base asset balance to sell.
4. Mark the AlphaSquared action `executed=True` only after Coinbase accepts the order.

By default, the runner resolves your Coinbase default portfolio and uses that portfolio for balance lookup and order placement. To run against a specific Coinbase portfolio, pass its UUID:

```python
results = trader.execute_pending_strategy_actions(
    "BTC-USDC",
    strategy_name="My Custom Strategy",
    portfolio_uuid="YOUR_COINBASE_PORTFOLIO_UUID"
)
```

The runner also sends a deterministic Coinbase `client_order_id` derived from the AlphaSquared action. This helps Coinbase return the existing order if the same action is retried after a timeout or scheduled job retry.

For simple scheduled jobs, run one worker at a time and poll `executed=False`. If you intentionally run multiple workers in parallel, add your own coordination layer such as reserved cloud concurrency or a storage-backed lock.

The older `trader.execute_strategy(product_id, strategy_name)` risk-value helper remains available for compatibility, but action polling is the better fit when AlphaSquared is already emitting strategy actions.

## Documentation

For more information about the Coinbase Advanced Trader API, consult the [official API documentation](https://docs.cdp.coinbase.com/advanced-trade/docs/welcome).

## License

This project is licensed under the MIT License. See the LICENSE file for more information.

## Author

Rhett Reisman


GitHub: https://github.com/rhettre/coinbase-advancedtrade-python

## Disclaimer

This project is not affiliated with, maintained, or endorsed by Coinbase. Use this software at your own risk. Trading cryptocurrencies carries a risk of financial loss. The developers of this software are not responsible for any financial losses or damages incurred while using this software. Nothing in this software should be seen as an inducement to trade with a particular strategy or as financial advice.
