import unittest
from unittest.mock import Mock, patch
from decimal import Decimal

from coinbase_advanced_trader.models import Order, OrderSide, OrderType
from coinbase_advanced_trader.services.order_service import OrderService
from coinbase_advanced_trader.services.price_service import PriceService


class TestOrderService(unittest.TestCase):
    """Test cases for the OrderService class."""

    def setUp(self):
        """Set up the test environment before each test method."""
        self.rest_client_mock = Mock()
        self.price_service_mock = Mock(spec=PriceService)
        self.order_service = OrderService(self.rest_client_mock, self.price_service_mock)

    def test_fiat_market_buy(self):
        """Test the fiat_market_buy method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        mock_response = {
            'success': True,
            'order_id': '007e54c1-9e53-4afc-93f1-92cd5e98bc20',
            'success_response': {
                'order_id': '007e54c1-9e53-4afc-93f1-92cd5e98bc20',
                'product_id': 'BTC-USDC',
                'side': 'BUY',
                'client_order_id': '1234567890'
            },
            'order_configuration': {'market_market_ioc': {'quote_size': '10'}}
        }
        self.rest_client_mock.market_order_buy.return_value = mock_response

        order = self.order_service.fiat_market_buy(product_id, fiat_amount)

        self.assertIsInstance(order, Order)
        self.assertEqual(order.id, '007e54c1-9e53-4afc-93f1-92cd5e98bc20')
        self.assertEqual(order.product_id, 'BTC-USDC')
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.type, OrderType.MARKET)
        self.assertEqual(order.size, Decimal('10'))

    def test_fiat_market_sell(self):
        """Test the fiat_market_sell method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        mock_spot_price = Decimal('50000')
        mock_product_details = {'base_increment': '0.00000001'}
        self.price_service_mock.get_spot_price.return_value = mock_spot_price
        self.price_service_mock.get_product_details.return_value = mock_product_details

        mock_response = {
            'success': True,
            'order_id': '007e54c1-9e53-4afc-93f1-92cd5e98bc20',
            'success_response': {
                'order_id': '007e54c1-9e53-4afc-93f1-92cd5e98bc20',
                'product_id': 'BTC-USDC',
                'side': 'SELL',
                'client_order_id': '1234567890'
            },
            'order_configuration': {'market_market_ioc': {'base_size': '0.00020000'}}
        }
        self.rest_client_mock.market_order_sell.return_value = mock_response

        order = self.order_service.fiat_market_sell(product_id, fiat_amount)

        self.assertIsInstance(order, Order)
        self.assertEqual(order.id, '007e54c1-9e53-4afc-93f1-92cd5e98bc20')
        self.assertEqual(order.product_id, 'BTC-USDC')
        self.assertEqual(order.side, OrderSide.SELL)
        self.assertEqual(order.type, OrderType.MARKET)
        self.assertEqual(order.size, Decimal('0.00020000'))

    def test_fiat_limit_buy(self):
        """Test the fiat_limit_buy method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        price_multiplier = Decimal('0.9995')

        mock_spot_price = Decimal('50000')
        mock_product_details = {
            'base_increment': '0.00000001',
            'quote_increment': '0.01'
        }
        self.price_service_mock.get_spot_price.return_value = mock_spot_price
        self.price_service_mock.get_product_details.return_value = mock_product_details

        mock_response = {
            'success': True,
            'order_id': 'fb67bb54-73ba-41ec-a038-9883664325b7',
            'success_response': {
                'order_id': 'fb67bb54-73ba-41ec-a038-9883664325b7',
                'product_id': 'BTC-USDC',
                'side': 'BUY',
                'client_order_id': '12345678901'
            },
            'order_configuration': {
                'limit_limit_gtc': {
                    'base_size': '0.00020010',
                    'limit_price': '49975.00',
                    'post_only': False
                }
            }
        }
        self.rest_client_mock.limit_order_gtc_buy.return_value = mock_response

        order = self.order_service.fiat_limit_buy(product_id, fiat_amount, price_multiplier)

        self.assertIsInstance(order, Order)
        self.assertEqual(order.id, 'fb67bb54-73ba-41ec-a038-9883664325b7')
        self.assertEqual(order.product_id, 'BTC-USDC')
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.type, OrderType.LIMIT)
        self.assertEqual(order.size, Decimal('0.00020010'))
        self.assertEqual(order.price, Decimal('49975.00'))

    def test_fiat_limit_sell(self):
        """Test the fiat_limit_sell method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        price_multiplier = Decimal('1.005')

        mock_spot_price = Decimal('50000')
        mock_product_details = {
            'base_increment': '0.00000001',
            'quote_increment': '0.01'
        }
        self.price_service_mock.get_spot_price.return_value = mock_spot_price
        self.price_service_mock.get_product_details.return_value = mock_product_details

        mock_response = {
            'success': True,
            'order_id': 'fb67bb54-73ba-41ec-a038-9883664325b7',
            'success_response': {
                'order_id': 'fb67bb54-73ba-41ec-a038-9883664325b7',
                'product_id': 'BTC-USDC',
                'side': 'SELL',
                'client_order_id': '12345678901'
            },
            'order_configuration': {
                'limit_limit_gtc': {
                    'base_size': '0.00019900',
                    'limit_price': '50250.00',
                    'post_only': False
                }
            }
        }
        self.rest_client_mock.limit_order_gtc_sell.return_value = mock_response

        order = self.order_service.fiat_limit_sell(product_id, fiat_amount, price_multiplier)

        self.assertIsInstance(order, Order)
        self.assertEqual(order.id, 'fb67bb54-73ba-41ec-a038-9883664325b7')
        self.assertEqual(order.product_id, 'BTC-USDC')
        self.assertEqual(order.side, OrderSide.SELL)
        self.assertEqual(order.type, OrderType.LIMIT)
        self.assertEqual(order.size, Decimal('0.00019900'))
        self.assertEqual(order.price, Decimal('50250.00'))

    def test_place_limit_order(self):
        """Test the _place_limit_order method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        price_multiplier = Decimal('0.9995')
        side = OrderSide.BUY

        mock_spot_price = Decimal('50000')
        mock_product_details = {
            'base_increment': '0.00000001',
            'quote_increment': '0.01'
        }
        self.price_service_mock.get_spot_price.return_value = mock_spot_price
        self.price_service_mock.get_product_details.return_value = mock_product_details

        mock_response = {
            'success': True,
            'order_id': 'fb67bb54-73ba-41ec-a038-9883664325b7',
            'success_response': {
                'order_id': 'fb67bb54-73ba-41ec-a038-9883664325b7',
                'product_id': 'BTC-USDC',
                'side': 'BUY',
                'client_order_id': '12345678901'
            },
            'order_configuration': {
                'limit_limit_gtc': {
                    'base_size': '0.00020010',
                    'limit_price': '49975.00',
                    'post_only': False
                }
            }
        }
        self.rest_client_mock.limit_order_gtc_buy.return_value = mock_response

        order = self.order_service._place_limit_order(
            product_id, fiat_amount, price_multiplier, side
        )

        self.assertIsInstance(order, Order)
        self.assertEqual(order.id, 'fb67bb54-73ba-41ec-a038-9883664325b7')
        self.assertEqual(order.product_id, 'BTC-USDC')
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.type, OrderType.LIMIT)
        self.assertEqual(order.size, Decimal('0.00020010'))
        self.assertEqual(order.price, Decimal('49975.00'))

    @patch('coinbase_advanced_trader.services.order_service.logger')
    def test_log_order_result(self, mock_logger):
        """Test the _log_order_result method."""
        order_response = {
            'success': True,
            'order_id': 'fb67bb54-73ba-41ec-a038-9883664325b7',
            'success_response': {
                'order_id': 'fb67bb54-73ba-41ec-a038-9883664325b7',
                'product_id': 'BTC-USDC',
                'side': 'BUY',
                'client_order_id': '12345678901'
            },
            'order_configuration': {
                'limit_limit_gtc': {
                    'base_size': '0.00020010',
                    'limit_price': '49975.00',
                    'post_only': False
                }
            }
        }
        product_id = "BTC-USDC"
        amount = Decimal('0.00020010')
        price = Decimal('49975.00')
        side = OrderSide.BUY

        self.order_service._log_order_result(
            order_response, product_id, amount, price, side
        )

        mock_logger.info.assert_called_once_with(
            "Successfully placed a limit buy order for 0.00020010 BTC ($10.00) "
            "at a price of 49975.00 USDC."
        )
        mock_logger.debug.assert_called_once_with(f"Coinbase response: {order_response}")


if __name__ == '__main__':
    unittest.main()