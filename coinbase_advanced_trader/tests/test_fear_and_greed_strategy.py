import unittest
from unittest.mock import Mock, patch
from decimal import Decimal

from coinbase_advanced_trader.services.fear_and_greed_strategy import FearAndGreedStrategy
from coinbase_advanced_trader.models import Order, OrderSide, OrderType
from coinbase_advanced_trader.services.order_service import OrderService
from coinbase_advanced_trader.services.price_service import PriceService
from coinbase_advanced_trader.trading_config import FearAndGreedConfig


class TestFearAndGreedStrategy(unittest.TestCase):
    """Test cases for the FearAndGreedStrategy class."""

    def setUp(self):
        """Set up the test environment before each test method."""
        self.order_service_mock = Mock(spec=OrderService)
        self.price_service_mock = Mock(spec=PriceService)
        self.config_mock = Mock(spec=FearAndGreedConfig)
        self.strategy = FearAndGreedStrategy(
            self.order_service_mock,
            self.price_service_mock,
            self.config_mock
        )

    @patch('coinbase_advanced_trader.services.fear_and_greed_strategy.requests.get')
    def test_execute_trade_buy(self, mock_get):
        """Test execute_trade method for a buy scenario."""
        mock_get.return_value.json.return_value = {
            'data': [{'value': '25', 'value_classification': 'Extreme Fear'}]
        }

        self.config_mock.get_fgi_schedule.return_value = [
            {'threshold': 30, 'factor': 1.2, 'action': 'buy'},
            {'threshold': 70, 'factor': 0.8, 'action': 'sell'}
        ]

        mock_order = Order(
            id='fb67bb54-73ba-41ec-a038-9883664325b7',
            product_id='BTC-USDC',
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            size=Decimal('0.0002'),
            price=Decimal('50000.00')
        )
        self.order_service_mock.fiat_limit_buy.return_value = mock_order

        result = self.strategy.execute_trade('BTC-USDC', '10')

        self.assertEqual(result, mock_order)
        self.order_service_mock.fiat_limit_buy.assert_called_once()
        call_args = self.order_service_mock.fiat_limit_buy.call_args
        self.assertEqual(call_args[0][0], 'BTC-USDC')
        self.assertAlmostEqual(Decimal(call_args[0][1]), Decimal('12.00'), places=8)
        mock_get.assert_called_once()
        self.config_mock.get_fgi_schedule.assert_called_once()

    @patch('coinbase_advanced_trader.services.fear_and_greed_strategy.requests.get')
    def test_execute_trade_sell(self, mock_get):
        """Test execute_trade method for a sell scenario."""
        mock_get.return_value.json.return_value = {
            'data': [{'value': '75', 'value_classification': 'Extreme Greed'}]
        }

        self.config_mock.get_fgi_schedule.return_value = [
            {'threshold': 30, 'factor': 1.2, 'action': 'buy'},
            {'threshold': 70, 'factor': 0.8, 'action': 'sell'}
        ]

        mock_order = Order(
            id='fb67bb54-73ba-41ec-a038-9883664325b7',
            product_id='BTC-USDC',
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            size=Decimal('0.0002'),
            price=Decimal('50000.00')
        )
        self.order_service_mock.fiat_limit_sell.return_value = mock_order

        result = self.strategy.execute_trade('BTC-USDC', '10')

        self.assertEqual(result, mock_order)
        self.order_service_mock.fiat_limit_sell.assert_called_once()
        call_args = self.order_service_mock.fiat_limit_sell.call_args
        self.assertEqual(call_args[0][0], 'BTC-USDC')
        self.assertAlmostEqual(Decimal(call_args[0][1]), Decimal('8.00'), places=8)
        mock_get.assert_called_once()
        self.config_mock.get_fgi_schedule.assert_called_once()

    @patch('coinbase_advanced_trader.services.fear_and_greed_strategy.requests.get')
    def test_execute_trade_no_condition_met(self, mock_get):
        """Test execute_trade method when no condition is met."""
        mock_get.return_value.json.return_value = {
            'data': [{'value': '50', 'value_classification': 'Neutral'}]
        }

        self.config_mock.get_fgi_schedule.return_value = [
            {'threshold': 30, 'factor': 1.2, 'action': 'buy'},
            {'threshold': 70, 'factor': 0.8, 'action': 'sell'}
        ]

        result = self.strategy.execute_trade('BTC-USDC', '10')

        self.assertIsNone(result)
        self.order_service_mock.fiat_limit_buy.assert_not_called()
        self.order_service_mock.fiat_limit_sell.assert_not_called()
        mock_get.assert_called_once()
        self.config_mock.get_fgi_schedule.assert_called_once()

    @patch('coinbase_advanced_trader.services.fear_and_greed_strategy.requests.get')
    def test_get_fear_and_greed_index(self, mock_get):
        """Test get_fear_and_greed_index method."""
        mock_get.return_value.json.return_value = {
            'data': [{'value': '47', 'value_classification': 'Neutral'}]
        }

        result = self.strategy.get_fear_and_greed_index()

        self.assertEqual(result, (47, 'Neutral'))
        mock_get.assert_called_once()


if __name__ == '__main__':
    unittest.main()