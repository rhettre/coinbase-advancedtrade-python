import unittest
from unittest.mock import Mock, patch
from decimal import Decimal

from coinbase.rest import RESTClient

from coinbase_advanced_trader.services.price_service import PriceService


class TestPriceService(unittest.TestCase):
    """Test cases for the PriceService class."""

    def setUp(self):
        """Set up the test environment before each test method."""
        self.rest_client_mock = Mock(spec=RESTClient)
        self.price_service = PriceService(self.rest_client_mock)

    def test_get_spot_price_success(self):
        """Test successful retrieval of spot price."""
        product_id = "BTC-USDC"
        mock_response = {
            'product_id': 'BTC-USDC',
            'price': '61536',
            'quote_increment': '0.01'
        }
        self.rest_client_mock.get_product.return_value = mock_response

        result = self.price_service.get_spot_price(product_id)

        self.rest_client_mock.get_product.assert_called_once_with(product_id)
        self.assertEqual(result, Decimal('61536.00'))

    def test_get_spot_price_missing_price(self):
        """Test handling of missing price in API response."""
        product_id = "BTC-USDC"
        mock_response = {
            'product_id': 'BTC-USDC',
            'quote_increment': '0.01'
        }
        self.rest_client_mock.get_product.return_value = mock_response

        result = self.price_service.get_spot_price(product_id)

        self.rest_client_mock.get_product.assert_called_once_with(product_id)
        self.assertIsNone(result)

    @patch('coinbase_advanced_trader.services.price_service.logger')
    def test_get_spot_price_exception(self, mock_logger):
        """Test error handling when fetching spot price."""
        product_id = "BTC-USDDC"
        self.rest_client_mock.get_product.side_effect = Exception(
            "Product not found"
        )

        result = self.price_service.get_spot_price(product_id)

        self.rest_client_mock.get_product.assert_called_once_with(product_id)
        self.assertIsNone(result)
        mock_logger.error.assert_called_once_with(
            "Error fetching spot price for BTC-USDDC: Product not found"
        )

    def test_get_product_details_success(self):
        """Test successful retrieval of product details."""
        product_id = "BTC-USDC"
        mock_response = {
            'product_id': 'BTC-USDC',
            'base_increment': '0.00000001',
            'quote_increment': '0.01'
        }
        self.rest_client_mock.get_product.return_value = mock_response

        result = self.price_service.get_product_details(product_id)

        self.rest_client_mock.get_product.assert_called_once_with(product_id)
        expected_result = {
            'base_increment': Decimal('0.00000001'),
            'quote_increment': Decimal('0.01')
        }
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()