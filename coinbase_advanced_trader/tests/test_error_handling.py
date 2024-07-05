import unittest
from unittest.mock import Mock, patch

from coinbase.rest import RESTClient

from coinbase_advanced_trader.services.order_service import OrderService
from coinbase_advanced_trader.services.price_service import PriceService


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling in OrderService."""

    def setUp(self):
        """Set up the test environment before each test method."""
        self.rest_client_mock = Mock(spec=RESTClient)
        self.price_service_mock = Mock(spec=PriceService)
        self.order_service = OrderService(
            self.rest_client_mock, self.price_service_mock
        )

    @patch('coinbase_advanced_trader.services.order_service.logger')
    def test_invalid_product_id(self, mock_logger):
        """Test handling of invalid product ID."""
        product_id = "BTC-USDDC"
        fiat_amount = "100"
        
        self.rest_client_mock.market_order_buy.side_effect = Exception(
            "Invalid product_id"
        )

        with self.assertRaises(Exception):
            self.order_service.fiat_market_buy(product_id, fiat_amount)

        mock_logger.error.assert_called_with(
            "Failed to place a market buy order. "
            "Reason: Invalid product_id. "
            "Preview failure reason: Unknown"
        )

    @patch('coinbase_advanced_trader.services.order_service.logger')
    def test_insufficient_funds(self, mock_logger):
        """Test handling of insufficient funds error."""
        product_id = "BTC-USDC"
        fiat_amount = "100000"
        
        error_response = {
            'success': False,
            'failure_reason': 'UNKNOWN_FAILURE_REASON',
            'order_id': '',
            'error_response': {
                'error': 'INSUFFICIENT_FUND',
                'message': 'Insufficient balance in source account',
                'error_details': '',
                'preview_failure_reason': 'PREVIEW_INSUFFICIENT_FUND'
            },
            'order_configuration': {'market_market_ioc': {'quote_size': '100000'}}
        }
        self.rest_client_mock.market_order_buy.return_value = error_response

        with self.assertRaises(Exception) as context:
            self.order_service.fiat_market_buy(product_id, fiat_amount)

        self.assertIn("Failed to place a market buy order", str(context.exception))
        mock_logger.error.assert_called_once_with(
            "Failed to place a market buy order. "
            "Reason: Insufficient balance in source account. "
            "Preview failure reason: PREVIEW_INSUFFICIENT_FUND"
        )

    @patch('coinbase_advanced_trader.services.order_service.logger')
    def test_quote_size_too_high(self, mock_logger):
        """Test handling of quote size too high error."""
        product_id = "BTC-USDC"
        fiat_amount = "100000000000000000000"
        
        error_response = {
            'success': False,
            'failure_reason': 'UNKNOWN_FAILURE_REASON',
            'order_id': '',
            'error_response': {
                'error': 'UNKNOWN_FAILURE_REASON',
                'message': '',
                'error_details': '',
                'preview_failure_reason': 'PREVIEW_INVALID_QUOTE_SIZE_TOO_LARGE'
            },
            'order_configuration': {
                'market_market_ioc': {'quote_size': '100000000000000000000'}
            }
        }
        self.rest_client_mock.market_order_buy.return_value = error_response

        with self.assertRaises(Exception) as context:
            self.order_service.fiat_market_buy(product_id, fiat_amount)

        self.assertIn("Failed to place a market buy order", str(context.exception))
        mock_logger.error.assert_called_once_with(
            "Failed to place a market buy order. "
            "Reason: . "
            "Preview failure reason: PREVIEW_INVALID_QUOTE_SIZE_TOO_LARGE"
        )


if __name__ == '__main__':
    unittest.main()