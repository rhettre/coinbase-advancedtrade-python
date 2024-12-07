import unittest
from unittest.mock import Mock, patch
from decimal import Decimal

from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient
from coinbase_advanced_trader.models import Order, OrderSide, OrderType
from coinbase_advanced_trader.services.order_service import OrderService
from coinbase_advanced_trader.services.price_service import PriceService
from coinbase_advanced_trader.services.fear_and_greed_strategy import FearAndGreedStrategy
from coinbase_advanced_trader.trading_config import FearAndGreedConfig


class TestEnhancedRESTClient(unittest.TestCase):
    """Test cases for the EnhancedRESTClient class."""

    def setUp(self):
        """Set up the test environment before each test method."""
        self.api_key = "test_api_key"
        self.api_secret = "test_api_secret"
        self.client = EnhancedRESTClient(self.api_key, self.api_secret)
        self.client._order_service = Mock(spec=OrderService)
        self.client._price_service = Mock(spec=PriceService)
        self.client._fear_and_greed_strategy = Mock(spec=FearAndGreedStrategy)
        self.client._config = Mock(spec=FearAndGreedConfig)

    def test_fiat_market_buy(self):
        """Test the fiat_market_buy method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        mock_order = Order(
            id='007e54c1-9e53-4afc-93f1-92cd5e98bc20',
            product_id=product_id,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            size=Decimal(fiat_amount)
        )
        self.client._order_service.fiat_market_buy.return_value = mock_order

        result = self.client.fiat_market_buy(product_id, fiat_amount)

        self.client._order_service.fiat_market_buy.assert_called_once_with(
            product_id, fiat_amount
        )
        self.assertEqual(result, mock_order)

    def test_fiat_market_sell(self):
        """Test the fiat_market_sell method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        mock_order = Order(
            id='007e54c1-9e53-4afc-93f1-92cd5e98bc20',
            product_id=product_id,
            side=OrderSide.SELL,
            type=OrderType.MARKET,
            size=Decimal('0.0002')
        )
        self.client._order_service.fiat_market_sell.return_value = mock_order

        result = self.client.fiat_market_sell(product_id, fiat_amount)

        self.client._order_service.fiat_market_sell.assert_called_once_with(
            product_id, fiat_amount
        )
        self.assertEqual(result, mock_order)

    def test_fiat_limit_buy(self):
        """Test the fiat_limit_buy method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        price_multiplier = 0.9995

        result = self.client.fiat_limit_buy(product_id, fiat_amount)
        
        self.client._order_service.fiat_limit_buy.assert_called_once_with(
            product_id, fiat_amount, None, price_multiplier
        )

    def test_fiat_limit_sell(self):
        """Test the fiat_limit_sell method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        price_multiplier = 1.005

        result = self.client.fiat_limit_sell(product_id, fiat_amount)
        
        self.client._order_service.fiat_limit_sell.assert_called_once_with(
            product_id, fiat_amount, None, price_multiplier
        )

    def test_trade_based_on_fgi(self):
        """Test the trade_based_on_fgi method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        mock_result = {"status": "success", "order_id": "123456"}
        self.client._fear_and_greed_strategy.execute_trade.return_value = mock_result

        result = self.client.trade_based_on_fgi(product_id, fiat_amount)

        self.client._fear_and_greed_strategy.execute_trade.assert_called_once()

        call_args = self.client._fear_and_greed_strategy.execute_trade.call_args
        self.assertEqual(call_args[0][0], product_id)
        self.assertAlmostEqual(Decimal(call_args[0][1]), Decimal(fiat_amount), places=8)
        self.assertEqual(result, mock_result)

    def test_update_fgi_schedule(self):
        """Test the update_fgi_schedule method."""
        new_schedule = [
            {'threshold': 20, 'factor': 1.2, 'action': 'buy'},
            {'threshold': 80, 'factor': 0.8, 'action': 'sell'}
        ]
        self.client._config.validate_schedule.return_value = True
        self.client._config.update_fgi_schedule.return_value = None

        result = self.client.update_fgi_schedule(new_schedule)

        self.client._config.validate_schedule.assert_called_once_with(new_schedule)
        self.client._config.update_fgi_schedule.assert_called_once_with(new_schedule)
        self.assertTrue(result)

    def test_get_fgi_schedule(self):
        """Test the get_fgi_schedule method."""
        mock_schedule = [
            {'threshold': 20, 'factor': 1.2, 'action': 'buy'},
            {'threshold': 80, 'factor': 0.8, 'action': 'sell'}
        ]
        self.client._config.get_fgi_schedule.return_value = mock_schedule

        result = self.client.get_fgi_schedule()

        self.client._config.get_fgi_schedule.assert_called_once()
        self.assertEqual(result, mock_schedule)

    def test_validate_fgi_schedule(self):
        """Test the validate_fgi_schedule method."""
        schedule = [
            {'threshold': 20, 'factor': 1.2, 'action': 'buy'},
            {'threshold': 80, 'factor': 0.8, 'action': 'sell'}
        ]
        self.client._config.validate_schedule.return_value = True

        result = self.client.validate_fgi_schedule(schedule)

        self.client._config.validate_schedule.assert_called_once_with(schedule)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()