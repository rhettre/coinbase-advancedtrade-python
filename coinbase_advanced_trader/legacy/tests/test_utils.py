import unittest
from unittest.mock import patch, MagicMock
from coinbase_advanced_trader.legacy.strategies.utils import get_spot_price


class TestGetSpotPrice(unittest.TestCase):
    @patch('coinbase_advanced_trader.legacy.strategies.utils.client.getProduct')
    def test_get_spot_price_success(self, mock_get_product):
        # Mock the getProduct function to return a successful response
        mock_get_product.return_value = {'price': '50000'}

        # Test the function with a product_id
        result = get_spot_price('BTC-USD')

        # Assert that the function returns the correct spot price
        self.assertEqual(result, 50000.0)

    @patch('coinbase_advanced_trader.legacy.strategies.utils.client.getProduct')
    def test_get_spot_price_failure(self, mock_get_product):
        # Mock the getProduct function to return a response without a 'price' field
        mock_get_product.return_value = {}

        # Test the function with a product_id
        result = get_spot_price('BTC-USD')

        # Assert that the function returns None when the 'price' field is missing
        self.assertIsNone(result)

    @patch('coinbase_advanced_trader.legacy.strategies.utils.client.getProduct')
    def test_get_spot_price_exception(self, mock_get_product):
        # Mock the getProduct function to raise an exception
        mock_get_product.side_effect = Exception('Test exception')

        # Test the function with a product_id
        result = get_spot_price('BTC-USD')

        # Assert that the function returns None when an exception is raised
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
