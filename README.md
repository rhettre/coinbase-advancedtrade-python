# Coinbase Advanced Trader API Python Wrapper

This project provides a Python wrapper for the Coinbase Advanced Trader API and an example AWS limit order script that uses the wrapper. The Coinbase Advanced Trader API allows users to access advanced trading functionality, such as placing and managing orders, accessing account information, and retrieving market data.

## Features

- Access account and portfolio information.
- Place and manage orders.
- Retrieve historical orders and fills.
- Access product information and market data.
- Perform advanced trading operations.

## Setup

   1. Clone this repository or download the source files.

   2. Install the required Python packages:

        ```bash
            pip install -r requirements.txt

   3. Set your API key and secret in config.py. To obtain your API key and secret, follow the steps below:
      - Log in to your Coinbase account.
      - Navigate to API settings.
      - Create a new API key with the appropriate permissions.
      - Copy the API key and secret to config.py.

## Usage

### Using the Python Wrapper

- Import the required functions and classes from `coinbase_api_wrapper.py` to interact with the Coinbase API:

    ```python 
        from coinbase_api_wrapper import listAccounts, getAccount, createOrder, cancelOrders, listOrders, listFills, getOrder, listProducts, getProduct, getProductCandles, getMarketTrades, getTransactionsSummary

- You can now use these functions to interact with the API. For example, to retrieve your accounts:

    ```python
        accounts = listAccounts()
        print(accounts)

## Documentation

For more information about the Coinbase Advanced Trader API, consult the [official API documentation](https://docs.cloud.coinbase.com/advanced-trade-api/docs/rest-api-overview/).

## Disclaimer

This project is not affiliated with, maintained, or endorsed by Coinbase. Use this software at your own risk. Trading cryptocurrencies carries a risk of financial loss. The developers of this software are not responsible for any financial losses or damages incurred while using this software.

