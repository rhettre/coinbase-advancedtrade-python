import unittest
from unittest.mock import patch
from datetime import datetime
from coinbase_advanced_trader.legacy.coinbase_client import (
    Method,
    listAccounts,
    getAccount,
    createOrder,
    cancelOrders,
    listOrders,
    listFills,
    getOrder,
    listProducts,
    getProduct,
    getProductCandles,
    getMarketTrades,
    getTransactionsSummary,
)


class TestCoinbaseClient(unittest.TestCase):
    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_list_accounts(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "accounts": [{
                "uuid": "8bfc20d7-f7c6-4422-bf07-8243ca4169fe",
                "name": "BTC Wallet",
                "currency": "BTC",
                "available_balance": {
                    "value": "1.23",
                    "currency": "BTC"
                },
                "default": False,
                "active": True,
                "created_at": "2021-05-31T09:59:59Z",
                "updated_at": "2021-05-31T09:59:59Z",
                "deleted_at": "2021-05-31T09:59:59Z",
                "type": "ACCOUNT_TYPE_UNSPECIFIED",
                "ready": True,
                "hold": {
                    "value": "1.23",
                    "currency": "BTC"
                }
            }],
            "has_next": True,
            "cursor": "789100",
            "size": 1
        }

        # Call the function with sample input
        result = listAccounts(limit=5, cursor=None)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('accounts', result)
        self.assertIsInstance(result['accounts'], list)
        self.assertEqual(len(result['accounts']), 1)
        account = result['accounts'][0]
        self.assertEqual(
            account['uuid'], "8bfc20d7-f7c6-4422-bf07-8243ca4169fe")
        self.assertEqual(account['name'], "BTC Wallet")
        self.assertEqual(account['currency'], "BTC")
        self.assertEqual(account['available_balance']['value'], "1.23")
        self.assertEqual(account['available_balance']['currency'], "BTC")
        self.assertFalse(account['default'])
        self.assertTrue(account['active'])
        self.assertEqual(account['created_at'], "2021-05-31T09:59:59Z")
        self.assertEqual(account['updated_at'], "2021-05-31T09:59:59Z")
        self.assertEqual(account['deleted_at'], "2021-05-31T09:59:59Z")
        self.assertEqual(account['type'], "ACCOUNT_TYPE_UNSPECIFIED")
        self.assertTrue(account['ready'])
        self.assertEqual(account['hold']['value'], "1.23")
        self.assertEqual(account['hold']['currency'], "BTC")
        self.assertTrue(result['has_next'])
        self.assertEqual(result['cursor'], "789100")
        self.assertEqual(result['size'], 1)

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_get_account(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "account": {
                "uuid": "8bfc20d7-f7c6-4422-bf07-8243ca4169fe",
                "name": "BTC Wallet",
                "currency": "BTC",
                "available_balance": {
                    "value": "1.23",
                    "currency": "BTC"
                },
                "default": False,
                "active": True,
                "created_at": "2021-05-31T09:59:59Z",
                "updated_at": "2021-05-31T09:59:59Z",
                "deleted_at": "2021-05-31T09:59:59Z",
                "type": "ACCOUNT_TYPE_UNSPECIFIED",
                "ready": True,
                "hold": {
                    "value": "1.23",
                    "currency": "BTC"
                }
            }
        }

        # Call the function with sample input
        account_uuid = "8bfc20d7-f7c6-4422-bf07-8243ca4169fe"
        result = getAccount(account_uuid)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('account', result)
        account = result['account']
        self.assertEqual(
            account['uuid'], "8bfc20d7-f7c6-4422-bf07-8243ca4169fe")
        self.assertEqual(account['name'], "BTC Wallet")
        self.assertEqual(account['currency'], "BTC")
        self.assertEqual(account['available_balance']['value'], "1.23")
        self.assertEqual(account['available_balance']['currency'], "BTC")
        self.assertFalse(account['default'])
        self.assertTrue(account['active'])
        self.assertEqual(account['created_at'], "2021-05-31T09:59:59Z")
        self.assertEqual(account['updated_at'], "2021-05-31T09:59:59Z")
        self.assertEqual(account['deleted_at'], "2021-05-31T09:59:59Z")
        self.assertEqual(account['type'], "ACCOUNT_TYPE_UNSPECIFIED")
        self.assertTrue(account['ready'])
        self.assertEqual(account['hold']['value'], "1.23")
        self.assertEqual(account['hold']['currency'], "BTC")

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_createOrder(self, mock_cb_auth):
        # Mock the cb_auth function to return a sample response
        mock_cb_auth.return_value = {'result': 'success'}

        # Test the createOrder function
        client_order_id = 'example_order_id'
        product_id = 'BTC-USD'
        side = 'buy'
        order_type = 'limit_limit_gtc'
        order_configuration = {
            'limit_price': '30000.00',
            'base_size': '0.01',
            'post_only': True
        }

        result = createOrder(
            client_order_id=client_order_id,
            product_id=product_id,
            side=side,
            order_type=order_type,
            order_configuration=order_configuration
        )

        # Check that the cb_auth function was called with the correct arguments
        expected_payload = {
            'client_order_id': client_order_id,
            'product_id': product_id,
            'side': side,
            'order_configuration': {
                order_type: order_configuration
            }
        }
        mock_cb_auth.assert_called_with(Method.POST.value, '/api/v3/brokerage/orders', expected_payload)

        # Check that the createOrder function returns the response from cb_auth
        self.assertEqual(result, {'result': 'success'})
    
    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_cancel_orders(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "results": {
                "success": True,
                "failure_reason": "UNKNOWN_CANCEL_FAILURE_REASON",
                "order_id": "0000-00000"
            }
        }

        # Call the function with sample input
        order_ids = ["0000-00000"]
        result = cancelOrders(order_ids)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('results', result)
        results = result['results']
        self.assertTrue(results['success'])
        self.assertEqual(results['failure_reason'],
                         "UNKNOWN_CANCEL_FAILURE_REASON")
        self.assertEqual(results['order_id'], "0000-00000")

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_list_orders(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "orders": {
                "order_id": "0000-000000-000000",
                "product_id": "BTC-USD",
                "user_id": "2222-000000-000000",
                "order_configuration": {
                    # Sample order configuration data
                },
                "side": "UNKNOWN_ORDER_SIDE",
                "client_order_id": "11111-000000-000000",
                "status": "OPEN",
                "time_in_force": "UNKNOWN_TIME_IN_FORCE",
                "created_time": "2021-05-31T09:59:59Z",
                "completion_percentage": "50",
                "filled_size": "0.001",
                "average_filled_price": "50",
                "fee": "string",
                "number_of_fills": "2",
                "filled_value": "10000",
                "pending_cancel": True,
                "size_in_quote": False,
                "total_fees": "5.00",
                "size_inclusive_of_fees": False,
                "total_value_after_fees": "string",
                "trigger_status": "UNKNOWN_TRIGGER_STATUS",
                "order_type": "UNKNOWN_ORDER_TYPE",
                "reject_reason": "REJECT_REASON_UNSPECIFIED",
                "settled": "boolean",
                "product_type": "SPOT",
                "reject_message": "string",
                "cancel_message": "string",
                "order_placement_source": "RETAIL_ADVANCED"
            },
            "sequence": "string",
            "has_next": True,
            "cursor": "789100"
        }

        # Call the function with sample input
        result = listOrders()

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('orders', result)
        self.assertIn('sequence', result)
        self.assertIn('has_next', result)
        self.assertIn('cursor', result)
        self.assertTrue(result['has_next'])
        self.assertEqual(result['cursor'], '789100')

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_list_fills(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "fills": {
                "entry_id": "22222-2222222-22222222",
                "trade_id": "1111-11111-111111",
                "order_id": "0000-000000-000000",
                "trade_time": "2021-05-31T09:59:59Z",
                "trade_type": "FILL",
                "price": "10000.00",
                "size": "0.001",
                "commission": "1.25",
                "product_id": "BTC-USD",
                "sequence_timestamp": "2021-05-31T09:58:59Z",
                "liquidity_indicator": "UNKNOWN_LIQUIDITY_INDICATOR",
                "size_in_quote": False,
                "user_id": "3333-333333-3333333",
                "side": "UNKNOWN_ORDER_SIDE"
            },
            "cursor": "789100"
        }

        # Call the function with sample input
        result = listFills(order_id="0000-000000-000000", product_id="BTC-USD")

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('fills', result)

        fill = result['fills']
        self.assertEqual(fill['entry_id'], "22222-2222222-22222222")
        self.assertEqual(fill['trade_id'], "1111-11111-111111")
        self.assertEqual(fill['order_id'], "0000-000000-000000")
        self.assertEqual(fill['trade_time'], "2021-05-31T09:59:59Z")
        self.assertEqual(fill['trade_type'], "FILL")
        self.assertEqual(fill['price'], "10000.00")
        self.assertEqual(fill['size'], "0.001")
        self.assertEqual(fill['commission'], "1.25")
        self.assertEqual(fill['product_id'], "BTC-USD")
        self.assertEqual(fill['sequence_timestamp'], "2021-05-31T09:58:59Z")
        self.assertEqual(fill['liquidity_indicator'],
                         "UNKNOWN_LIQUIDITY_INDICATOR")
        self.assertFalse(fill['size_in_quote'])
        self.assertEqual(fill['user_id'], "3333-333333-3333333")
        self.assertEqual(fill['side'], "UNKNOWN_ORDER_SIDE")

        self.assertEqual(result['cursor'], "789100")

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_get_order(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "order": {
                "order_id": "0000-000000-000000",
                "product_id": "BTC-USD",
                "user_id": "2222-000000-000000",
                "order_configuration": {
                    # Sample order configuration data
                },
                "side": "UNKNOWN_ORDER_SIDE",
                "client_order_id": "11111-000000-000000",
                "status": "OPEN",
                "time_in_force": "UNKNOWN_TIME_IN_FORCE",
                "created_time": "2021-05-31T09:59:59Z",
                "completion_percentage": "50",
                "filled_size": "0.001",
                "average_filled_price": "50",
                "fee": "string",
                "number_of_fills": "2",
                "filled_value": "10000",
                "pending_cancel": True,
                "size_in_quote": False,
                "total_fees": "5.00",
                "size_inclusive_of_fees": False,
                "total_value_after_fees": "string",
                "trigger_status": "UNKNOWN_TRIGGER_STATUS",
                "order_type": "UNKNOWN_ORDER_TYPE",
                "reject_reason": "REJECT_REASON_UNSPECIFIED",
                "settled": "boolean",
                "product_type": "SPOT",
                "reject_message": "string",
                "cancel_message": "string",
                "order_placement_source": "RETAIL_ADVANCED"
            }
        }

        # Call the function with sample input
        order_id = "0000-000000-000000"
        result = getOrder(order_id)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        self.assertEqual(result['order']['order_id'], order_id)
        self.assertEqual(result['order']['product_id'], 'BTC-USD')
        self.assertEqual(result['order']['status'], 'OPEN')

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_list_products(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "products": {
                "product_id": "BTC-USD",
                "price": "140.21",
                "price_percentage_change_24h": "9.43%",
                "volume_24h": "1908432",
                "volume_percentage_change_24h": "9.43%",
                "base_increment": "0.00000001",
                "quote_increment": "0.00000001",
                "quote_min_size": "0.00000001",
                "quote_max_size": "1000",
                "base_min_size": "0.00000001",
                "base_max_size": "1000",
                "base_name": "Bitcoin",
                "quote_name": "US Dollar",
                "watched": True,
                "is_disabled": False,
                "new": True,
                "status": "string",
                "cancel_only": True,
                "limit_only": True,
                "post_only": True,
                "trading_disabled": False,
                "auction_mode": True,
                "product_type": "SPOT",
                "quote_currency_id": "USD",
                "base_currency_id": "BTC",
                "mid_market_price": "140.22",
                "base_display_symbol": "BTC",
                "quote_display_symbol": "USD"
            },
            "num_products": 100
        }

        # Call the function with sample input
        limit = 10
        offset = 0
        product_type = 'SPOT'
        result = listProducts(limit=limit, offset=offset,
                              product_type=product_type)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('products', result)
        self.assertIn('num_products', result)
        self.assertEqual(result['products']['product_id'], 'BTC-USD')
        self.assertEqual(result['num_products'], 100)

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_get_product(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "product_id": "BTC-USD",
            "price": "140.21",
            "price_percentage_change_24h": "9.43%",
            "volume_24h": "1908432",
            "volume_percentage_change_24h": "9.43%",
            "base_increment": "0.00000001",
            "quote_increment": "0.00000001",
            "quote_min_size": "0.00000001",
            "quote_max_size": "1000",
            "base_min_size": "0.00000001",
            "base_max_size": "1000",
            "base_name": "Bitcoin",
            "quote_name": "US Dollar",
            "watched": True,
            "is_disabled": False,
            "new": True,
            "status": "string",
            "cancel_only": True,
            "limit_only": True,
            "post_only": True,
            "trading_disabled": False,
            "auction_mode": True,
            "product_type": "SPOT",
            "quote_currency_id": "USD",
            "base_currency_id": "BTC",
            "mid_market_price": "140.22",
            "base_display_symbol": "BTC",
            "quote_display_symbol": "USD"
        }

        # Call the function with sample input
        product_id = 'BTC-USD'
        result = getProduct(product_id=product_id)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['product_id'], 'BTC-USD')
        self.assertEqual(result['price'], '140.21')
        self.assertEqual(result['base_name'], 'Bitcoin')
        self.assertEqual(result['quote_name'], 'US Dollar')

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_get_product_candles(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "candles": {
                "start": "1639508050",
                "low": "140.21",
                "high": "140.21",
                "open": "140.21",
                "close": "140.21",
                "volume": "56437345"
            }
        }

        # Call the function with sample input
        product_id = "BTC-USD"
        start = "1639508050"
        end = "1639511650"
        granularity = "3600"

        result = getProductCandles(product_id, start, end, granularity)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn("candles", result)
        self.assertEqual(result["candles"]["start"], start)
        self.assertEqual(result["candles"]["low"], "140.21")
        self.assertEqual(result["candles"]["high"], "140.21")
        self.assertEqual(result["candles"]["open"], "140.21")
        self.assertEqual(result["candles"]["close"], "140.21")
        self.assertEqual(result["candles"]["volume"], "56437345")

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_get_market_trades(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "trades": {
                "trade_id": "34b080bf-fcfd-445a-832b-46b5ddc65601",
                "product_id": "BTC-USD",
                "price": "140.91",
                "size": "4",
                "time": "2021-05-31T09:59:59Z",
                "side": "UNKNOWN_ORDER_SIDE",
                "bid": "291.13",
                "ask": "292.40"
            },
            "best_bid": "291.13",
            "best_ask": "292.40"
        }

        # Call the function with sample input
        product_id = "BTC-USD"
        limit = 10
        result = getMarketTrades(product_id, limit)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn("trades", result)
        self.assertEqual(result["trades"]["trade_id"],
                         "34b080bf-fcfd-445a-832b-46b5ddc65601")
        self.assertEqual(result["trades"]["product_id"], product_id)
        self.assertEqual(result["trades"]["price"], "140.91")
        self.assertEqual(result["trades"]["size"], "4")
        self.assertEqual(result["trades"]["side"], "UNKNOWN_ORDER_SIDE")
        self.assertEqual(result["trades"]["bid"], "291.13")
        self.assertEqual(result["trades"]["ask"], "292.40")
        self.assertEqual(result["best_bid"], "291.13")
        self.assertEqual(result["best_ask"], "292.40")

    @patch('coinbase_advanced_trader.coinbase_client.cb_auth')
    def test_get_transactions_summary(self, mock_cb_auth):
        # Mock the response from the API
        mock_cb_auth.return_value = {
            "total_volume": 1000,
            "total_fees": 25,
            "fee_tier": {
                "pricing_tier": "<$10k",
                "usd_from": "0",
                "usd_to": "10,000",
                "taker_fee_rate": "0.0010",
                "maker_fee_rate": "0.0020"
            },
            "margin_rate": {
                "value": "string"
            },
            "goods_and_services_tax": {
                "rate": "string",
                "type": "INCLUSIVE"
            },
            "advanced_trade_only_volume": 1000,
            "advanced_trade_only_fees": 25,
            "coinbase_pro_volume": 1000,
            "coinbase_pro_fees": 25
        }
        # Call the function with sample input
        start_date = datetime.strptime(
            "2021-01-01T00:00:00Z", '%Y-%m-%dT%H:%M:%SZ')
        end_date = datetime.strptime(
            "2021-01-31T23:59:59Z", '%Y-%m-%dT%H:%M:%SZ')
        user_native_currency = "USD"
        product_type = "SPOT"
        result = getTransactionsSummary(
            start_date, end_date, user_native_currency, product_type)

        # Assert the expected output
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["total_volume"], 1000)
        self.assertEqual(result["total_fees"], 25)
        self.assertEqual(result["fee_tier"]["pricing_tier"], "<$10k")
        self.assertEqual(result["fee_tier"]["usd_from"], "0")
        self.assertEqual(result["fee_tier"]["usd_to"], "10,000")
        self.assertEqual(result["fee_tier"]["taker_fee_rate"], "0.0010")
        self.assertEqual(result["fee_tier"]["maker_fee_rate"], "0.0020")
        self.assertEqual(result["margin_rate"]["value"], "string")
        self.assertEqual(result["goods_and_services_tax"]["rate"], "string")
        self.assertEqual(result["goods_and_services_tax"]["type"], "INCLUSIVE")
        self.assertEqual(result["advanced_trade_only_volume"], 1000)
        self.assertEqual(result["advanced_trade_only_fees"], 25)
        self.assertEqual(result["coinbase_pro_volume"], 1000)
        self.assertEqual(result["coinbase_pro_fees"], 25)


if __name__ == '__main__':
    unittest.main()
