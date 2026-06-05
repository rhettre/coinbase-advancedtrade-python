import unittest
from unittest.mock import Mock, patch
from decimal import Decimal

from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient
from coinbase_advanced_trader.models import Order, OrderSide, OrderType
from coinbase_advanced_trader.services.order_service import OrderService
from coinbase_advanced_trader.services.price_service import PriceService
from coinbase_advanced_trader.services.fear_and_greed_strategy import FearAndGreedStrategy
from coinbase_advanced_trader.services.strategy_planner_service import (
    StrategyPlannerService,
    VolatilityTargetedTrendPlan,
)
from coinbase_advanced_trader.services.websocket_service import OrderEvent, WebsocketService
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
        self.client._websocket_service = Mock(spec=WebsocketService)
        self.client._strategy_planner_service = Mock(spec=StrategyPlannerService)
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
            product_id,
            fiat_amount,
            client_order_id=None,
            retail_portfolio_id=None
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
            product_id,
            fiat_amount,
            client_order_id=None,
            retail_portfolio_id=None
        )
        self.assertEqual(result, mock_order)

    def test_fiat_limit_buy(self):
        """Test the fiat_limit_buy method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        price_multiplier = 0.9995

        result = self.client.fiat_limit_buy(product_id, fiat_amount)
        
        self.client._order_service.fiat_limit_buy.assert_called_once_with(
            product_id,
            fiat_amount,
            None,
            price_multiplier,
            False,
            client_order_id=None,
            retail_portfolio_id=None
        )

    def test_fiat_limit_sell(self):
        """Test the fiat_limit_sell method."""
        product_id = "BTC-USDC"
        fiat_amount = "10"
        price_multiplier = 1.005

        result = self.client.fiat_limit_sell(product_id, fiat_amount)
        
        self.client._order_service.fiat_limit_sell.assert_called_once_with(
            product_id,
            fiat_amount,
            None,
            price_multiplier,
            False,
            client_order_id=None,
            retail_portfolio_id=None
        )

    def test_watch_ticker_delegates_to_websocket_service(self):
        """Test the watch_ticker helper delegates to the WebSocket service."""
        self.client.watch_ticker(["BTC-USDC"], seconds=5, print_prices=False)

        self.client._websocket_service.watch_ticker.assert_called_once_with(
            product_ids=["BTC-USDC"],
            seconds=5,
            callback=None,
            print_prices=False,
            retry=True,
            verbose=False,
        )

    def test_wait_for_order_fill_delegates_to_websocket_service(self):
        """Test the wait_for_order_fill helper delegates to the WebSocket service."""
        self.client.wait_for_order_fill("order-123", "BTC-USDC", timeout=60)

        self.client._websocket_service.wait_for_order_fill.assert_called_once_with(
            order_id="order-123",
            product_id="BTC-USDC",
            timeout=60,
            callback=None,
            include_heartbeats=True,
            retry=True,
            verbose=False,
        )

    def test_buy_then_limit_sell_on_fill_places_take_profit_order(self):
        """Test the buy, wait-for-fill, then limit-sell workflow."""
        buy_order = Order(
            id='buy-order-id',
            product_id='BTC-USDC',
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            size=Decimal('10')
        )
        fill = OrderEvent(
            order_id='buy-order-id',
            product_id='BTC-USDC',
            status='FILLED',
            side='BUY',
            filled_size=Decimal('0.0002'),
            average_filled_price=Decimal('50000'),
            filled_value=Decimal('10'),
            total_fees=Decimal('0.05'),
            raw_order={}
        )
        sell_order = Order(
            id='sell-order-id',
            product_id='BTC-USDC',
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            size=Decimal('0.0002'),
            price=Decimal('52500.00')
        )
        self.client._order_service.fiat_market_buy.return_value = buy_order
        self.client._websocket_service.place_order_and_wait_for_fill.side_effect = (
            lambda product_id, place_order, timeout, callback: (place_order(), fill)
        )
        self.client._order_service.limit_sell_base_size.return_value = sell_order

        result = self.client.buy_then_limit_sell_on_fill(
            product_id='BTC-USDC',
            fiat_amount='10',
            sell_price_multiplier='1.05',
            timeout=60
        )

        self.client._order_service.fiat_market_buy.assert_called_once_with(
            'BTC-USDC',
            '10',
            client_order_id=None,
            retail_portfolio_id=None
        )
        self.client._websocket_service.place_order_and_wait_for_fill.assert_called_once()
        self.client._order_service.limit_sell_base_size.assert_called_once_with(
            'BTC-USDC',
            '0.0002',
            '52500.00',
            False,
            client_order_id=None,
            retail_portfolio_id=None
        )
        self.assertEqual(result['buy_order'], buy_order)
        self.assertEqual(result['fill'], fill)
        self.assertEqual(result['sell_order'], sell_order)
        self.assertEqual(result['sell_limit_price'], Decimal('52500.00'))

    def test_build_volatility_targeted_trend_plan_delegates_to_strategy_planner(self):
        """Test the volatility-targeted trend planner delegates to the service."""
        expected_plan = VolatilityTargetedTrendPlan(
            product_id='BTC-USDC',
            signal='BUY',
            latest_close=Decimal('50000'),
            trend_return=Decimal('0.1000'),
            realized_annual_volatility=Decimal('0.4000'),
            target_annual_volatility=Decimal('0.0800'),
            exposure_fraction=Decimal('0.2000'),
            max_quote_budget=Decimal('100'),
            target_quote_notional=Decimal('20.00'),
            candles_used=121,
            lookback_days=120,
            momentum_days=30,
            reason='test'
        )
        planner = self.client._strategy_planner_service
        planner.build_volatility_targeted_trend_plan.return_value = expected_plan

        result = self.client.build_volatility_targeted_trend_plan(
            product_id='BTC-USDC',
            quote_budget='100',
            lookback_days=120,
            momentum_days=30,
            target_annual_volatility='0.08',
            max_exposure_fraction='1',
        )

        planner.build_volatility_targeted_trend_plan.assert_called_once_with(
            product_id='BTC-USDC',
            quote_budget='100',
            lookback_days=120,
            momentum_days=30,
            target_annual_volatility='0.08',
            max_exposure_fraction='1',
        )
        self.assertEqual(result, expected_plan)

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

    def test_trade_based_on_fgi_ladder_delegates_to_strategy(self):
        """Test the static Fear & Greed ladder delegates to the strategy service."""
        expected = {'status': 'executed', 'action': 'buy'}
        self.client._fear_and_greed_strategy.execute_static_ladder.return_value = expected

        result = self.client.trade_based_on_fgi_ladder(
            product_id='BTC-USDC',
            portfolio_uuid='portfolio-1',
            base_amount='1.00',
            ladder=[{'max': 24, 'action': 'buy', 'amount': '2.00'}],
            trade_date='2026-01-01',
            job_name='fear_and_greed',
            post_only=True,
        )

        self.client._fear_and_greed_strategy.execute_static_ladder.assert_called_once_with(
            product_id='BTC-USDC',
            portfolio_uuid='portfolio-1',
            base_amount='1.00',
            ladder=[{'max': 24, 'action': 'buy', 'amount': '2.00'}],
            trade_date='2026-01-01',
            job_name='fear_and_greed',
            post_only=True,
        )
        self.assertEqual(result, expected)

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
