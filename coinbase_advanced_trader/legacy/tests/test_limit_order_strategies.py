import unittest
from unittest.mock import patch
from decimal import Decimal
from coinbase_advanced_trader.legacy.strategies.limit_order_strategies import fiat_limit_buy, fiat_limit_sell


class TestLimitOrderStrategies(unittest.TestCase):

    @patch('coinbase_advanced_trader.legacy.strategies.limit_order_strategies.getProduct')
    @patch('coinbase_advanced_trader.legacy.strategies.limit_order_strategies.get_spot_price')
    @patch('coinbase_advanced_trader.legacy.strategies.limit_order_strategies.createOrder')
    @patch('coinbase_advanced_trader.legacy.strategies.limit_order_strategies.generate_client_order_id')
    def test_fiat_limit_buy(self, mock_generate_client_order_id, mock_createOrder, mock_get_spot_price, mock_getProduct):
        # Mock the dependencies
        mock_getProduct.return_value = {
            'quote_increment': '0.01', 'base_increment': '0.00000001'}
        mock_get_spot_price.return_value = '28892.56'
        mock_generate_client_order_id.return_value = 'example_order_id'
        mock_createOrder.return_value = {'result': 'success'}

        # Test the function
        result = fiat_limit_buy("BTC-USD", 200)
        self.assertEqual(result['result'], 'success')

    @patch('coinbase_advanced_trader.legacy.strategies.limit_order_strategies.getProduct')
    @patch('coinbase_advanced_trader.legacy.strategies.limit_order_strategies.get_spot_price')
    @patch('coinbase_advanced_trader.legacy.strategies.limit_order_strategies.createOrder')
    @patch('coinbase_advanced_trader.legacy.strategies.limit_order_strategies.generate_client_order_id')
    def test_fiat_limit_sell(self, mock_generate_client_order_id, mock_createOrder, mock_get_spot_price, mock_getProduct):
        # Mock the dependencies
        mock_getProduct.return_value = {
            'quote_increment': '0.01', 'base_increment': '0.00000001'}
        mock_get_spot_price.return_value = '28892.56'
        mock_generate_client_order_id.return_value = 'example_order_id'
        mock_createOrder.return_value = {'result': 'success'}

        # Test the function
        result = fiat_limit_sell("BTC-USD", 200)
        self.assertEqual(result['result'], 'success')


if __name__ == '__main__':
    unittest.main()
