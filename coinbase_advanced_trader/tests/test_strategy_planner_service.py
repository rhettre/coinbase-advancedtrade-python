import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

from coinbase.rest import RESTClient

from coinbase_advanced_trader.services.strategy_planner_service import (
    StrategyPlannerService,
)


class TestStrategyPlannerService(unittest.TestCase):
    def setUp(self):
        self.rest_client_mock = Mock(spec=RESTClient)
        self.service = StrategyPlannerService(self.rest_client_mock)
        self.now = datetime(2026, 5, 4, tzinfo=timezone.utc)

    def test_build_volatility_targeted_trend_plan_positive_trend(self):
        self.rest_client_mock.get_public_candles.return_value = {
            "candles": [
                {
                    "start": str(index),
                    "close": str(100 + index),
                    "low": "1",
                    "high": "1",
                    "open": "1",
                    "volume": "1",
                }
                for index in range(31)
            ]
        }

        plan = self.service.build_volatility_targeted_trend_plan(
            product_id="BTC-USDC",
            quote_budget="100",
            lookback_days=30,
            momentum_days=10,
            target_annual_volatility="0.08",
            max_exposure_fraction="1",
            now=self.now,
        )

        self.assertEqual(plan.product_id, "BTC-USDC")
        self.assertEqual(plan.signal, "BUY")
        self.assertGreater(plan.trend_return, Decimal("0"))
        self.assertGreater(plan.target_quote_notional, Decimal("0"))
        self.assertLessEqual(plan.exposure_fraction, Decimal("1"))
        self.rest_client_mock.get_public_candles.assert_called_once()

    def test_build_volatility_targeted_trend_plan_negative_trend_reduces(self):
        self.rest_client_mock.get_public_candles.return_value = {
            "candles": [
                {
                    "start": str(index),
                    "close": str(130 - index),
                    "low": "1",
                    "high": "1",
                    "open": "1",
                    "volume": "1",
                }
                for index in range(31)
            ]
        }

        plan = self.service.build_volatility_targeted_trend_plan(
            product_id="BTC-USDC",
            quote_budget="100",
            lookback_days=30,
            momentum_days=10,
            now=self.now,
        )

        self.assertEqual(plan.signal, "REDUCE")
        self.assertEqual(plan.target_quote_notional, Decimal("0.00"))

    def test_build_volatility_targeted_trend_plan_rejects_too_few_candles(self):
        self.rest_client_mock.get_public_candles.return_value = {
            "candles": [{"start": "1", "close": "100"}]
        }

        with self.assertRaises(ValueError):
            self.service.build_volatility_targeted_trend_plan(
                product_id="BTC-USDC",
                quote_budget="100",
                lookback_days=30,
                momentum_days=10,
                now=self.now,
            )


if __name__ == "__main__":
    unittest.main()
