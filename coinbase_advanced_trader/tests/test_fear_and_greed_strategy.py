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
        # Mock the FearAndGreedIndex client
        self.strategy._fgi_client = Mock()

    def test_execute_trade_buy(self):
        """Test execute_trade method for a buy scenario."""
        self.strategy._fgi_client.get_current_value.return_value = 25
        self.strategy._fgi_client.get_current_classification.return_value = "Extreme Fear"

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

    def test_execute_trade_sell(self):
        """Test execute_trade method for a sell scenario."""
        self.strategy._fgi_client.get_current_value.return_value = 75
        self.strategy._fgi_client.get_current_classification.return_value = "Extreme Greed"

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

    def test_execute_trade_no_condition_met(self):
        """Test execute_trade method when no condition is met."""
        self.strategy._fgi_client.get_current_value.return_value = 50
        self.strategy._fgi_client.get_current_classification.return_value = "Neutral"

        self.config_mock.get_fgi_schedule.return_value = [
            {'threshold': 30, 'factor': 1.2, 'action': 'buy'},
            {'threshold': 70, 'factor': 0.8, 'action': 'sell'}
        ]

        result = self.strategy.execute_trade('BTC-USDC', '10')

        self.assertIsNone(result)
        self.order_service_mock.fiat_limit_buy.assert_not_called()
        self.order_service_mock.fiat_limit_sell.assert_not_called()

    def test_execute_static_ladder_buy_static_amount(self):
        """Test static ladder buys a fixed quote amount in fear."""
        self.strategy._fgi_client.get_current_value.return_value = 20
        self.strategy._fgi_client.get_current_classification.return_value = "Extreme Fear"
        mock_order = Order(
            id='buy-order',
            product_id='BTC-USDC',
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            size=Decimal('0.00004'),
            price=Decimal('50000.00'),
            client_order_id='client-id'
        )
        self.order_service_mock.fiat_limit_buy.return_value = mock_order

        result = self.strategy.execute_static_ladder(
            product_id='BTC-USDC',
            portfolio_uuid='portfolio-1',
            trade_date='2026-01-01',
            job_name='fear_and_greed'
        )

        self.assertEqual(result['status'], 'executed')
        self.assertEqual(result['action'], 'buy')
        self.assertEqual(result['quote_amount'], '2.00')
        self.order_service_mock.fiat_limit_buy.assert_called_once()
        _, kwargs = self.order_service_mock.fiat_limit_buy.call_args
        self.assertEqual(kwargs['retail_portfolio_id'], 'portfolio-1')
        self.assertIsNotNone(kwargs['client_order_id'])

    def test_execute_static_ladder_sell_static_amount(self):
        """Test static ladder sells a fixed quote amount in greed."""
        account_service = Mock()
        account_service.get_crypto_balance.return_value = Decimal('0.1')
        self.strategy.account_service = account_service
        self.strategy._fgi_client.get_current_value.return_value = 80
        self.strategy._fgi_client.get_current_classification.return_value = "Extreme Greed"
        mock_order = Order(
            id='sell-order',
            product_id='BTC-USDC',
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            size=Decimal('0.00002'),
            price=Decimal('50000.00'),
            client_order_id='client-id'
        )
        self.order_service_mock.fiat_limit_sell.return_value = mock_order

        result = self.strategy.execute_static_ladder(
            product_id='BTC-USDC',
            portfolio_uuid='portfolio-1',
            trade_date='2026-01-01',
            job_name='fear_and_greed'
        )

        self.assertEqual(result['status'], 'executed')
        self.assertEqual(result['action'], 'sell')
        self.assertEqual(result['quote_amount'], '1.00')
        account_service.get_crypto_balance.assert_called_once_with(
            'BTC',
            retail_portfolio_id='portfolio-1'
        )
        self.order_service_mock.fiat_limit_sell.assert_called_once()
        args, kwargs = self.order_service_mock.fiat_limit_sell.call_args
        self.assertEqual(args[1], '1.00')
        self.assertEqual(kwargs['retail_portfolio_id'], 'portfolio-1')

    def test_execute_static_ladder_skips_without_sell_balance(self):
        """Test static ladder skips sells when there is no base balance."""
        account_service = Mock()
        account_service.get_crypto_balance.return_value = Decimal('0')
        self.strategy.account_service = account_service
        self.strategy._fgi_client.get_current_value.return_value = 80
        self.strategy._fgi_client.get_current_classification.return_value = "Extreme Greed"

        result = self.strategy.execute_static_ladder(
            product_id='BTC-USDC',
            portfolio_uuid='portfolio-1',
            trade_date='2026-01-01',
            job_name='fear_and_greed'
        )

        self.assertEqual(result['status'], 'skipped')
        self.assertIn('No BTC balance', result['reason'])
        self.order_service_mock.fiat_limit_sell.assert_not_called()

    def test_execute_static_ladder_hold(self):
        """Test static ladder holds in the neutral zone."""
        self.strategy._fgi_client.get_current_value.return_value = 50
        self.strategy._fgi_client.get_current_classification.return_value = "Neutral"

        result = self.strategy.execute_static_ladder(
            product_id='BTC-USDC',
            portfolio_uuid='portfolio-1',
            trade_date='2026-01-01',
            job_name='fear_and_greed'
        )

        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['action'], None)
        self.order_service_mock.fiat_limit_buy.assert_not_called()
        self.order_service_mock.fiat_limit_sell.assert_not_called()


if __name__ == '__main__':
    unittest.main()
