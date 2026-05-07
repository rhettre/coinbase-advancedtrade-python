"""Risk-first strategy planning helpers for demo-friendly automation."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import sqrt
from statistics import pstdev
from typing import Any, Dict, List, Optional

from coinbase.rest import RESTClient

from coinbase_advanced_trader.utils import response_to_dict


@dataclass
class VolatilityTargetedTrendPlan:
    """A dry-run plan for a simple long-only volatility-targeted trend sleeve."""

    product_id: str
    signal: str
    latest_close: Decimal
    trend_return: Decimal
    realized_annual_volatility: Decimal
    target_annual_volatility: Decimal
    exposure_fraction: Decimal
    max_quote_budget: Decimal
    target_quote_notional: Decimal
    candles_used: int
    lookback_days: int
    momentum_days: int
    reason: str

    def as_dict(self) -> Dict[str, Any]:
        """Return a plain dict for printing or logging in tutorials."""
        return {
            "product_id": self.product_id,
            "signal": self.signal,
            "latest_close": str(self.latest_close),
            "trend_return": str(self.trend_return),
            "realized_annual_volatility": str(self.realized_annual_volatility),
            "target_annual_volatility": str(self.target_annual_volatility),
            "exposure_fraction": str(self.exposure_fraction),
            "max_quote_budget": str(self.max_quote_budget),
            "target_quote_notional": str(self.target_quote_notional),
            "candles_used": self.candles_used,
            "lookback_days": self.lookback_days,
            "momentum_days": self.momentum_days,
            "reason": self.reason,
        }


class StrategyPlannerService:
    """Build conservative, dry-run strategy plans on top of official REST data."""

    DAILY_GRANULARITY = "ONE_DAY"
    ANNUALIZATION_DAYS = Decimal("365")

    def __init__(self, rest_client: RESTClient):
        self.rest_client = rest_client

    def build_volatility_targeted_trend_plan(
        self,
        product_id: str,
        quote_budget: str,
        lookback_days: int = 120,
        momentum_days: int = 30,
        target_annual_volatility: str = "0.08",
        max_exposure_fraction: str = "1",
        now: Optional[datetime] = None,
    ) -> VolatilityTargetedTrendPlan:
        """
        Build a dry-run plan for a simple long-only trend sleeve.

        This helper intentionally does not place orders. It gives tutorials a
        conservative first strategy to discuss before any live execution:
        positive trend can hold a volatility-scaled long exposure; negative or
        flat trend means reduce exposure or stay in cash.
        """
        if lookback_days <= momentum_days:
            raise ValueError("lookback_days must be greater than momentum_days")
        if momentum_days <= 0:
            raise ValueError("momentum_days must be greater than 0")

        max_quote_budget = Decimal(str(quote_budget))
        target_vol = Decimal(str(target_annual_volatility))
        max_exposure = Decimal(str(max_exposure_fraction))

        if max_quote_budget <= 0:
            raise ValueError("quote_budget must be greater than 0")
        if target_vol <= 0:
            raise ValueError("target_annual_volatility must be greater than 0")
        if max_exposure <= 0:
            raise ValueError("max_exposure_fraction must be greater than 0")

        candles = self._fetch_daily_candles(product_id, lookback_days, now)
        closes = [
            Decimal(str(candle["close"]))
            for candle in candles
            if candle.get("close")
        ]

        minimum_candles = momentum_days + 1
        if len(closes) < minimum_candles:
            raise ValueError(
                f"Need at least {minimum_candles} candles for a {momentum_days}-day "
                f"momentum plan; got {len(closes)}."
            )

        latest_close = closes[-1]
        momentum_start_close = closes[-momentum_days - 1]
        if latest_close <= 0 or momentum_start_close <= 0:
            raise ValueError("Candle closes must be greater than 0")

        trend_return = (latest_close / momentum_start_close) - Decimal("1")
        realized_vol = self._annualized_volatility(closes)
        exposure_fraction = self._target_exposure_fraction(
            target_vol,
            realized_vol,
            max_exposure,
        )

        if trend_return > 0:
            signal = "BUY"
            target_quote_notional = (max_quote_budget * exposure_fraction).quantize(
                Decimal("0.01")
            )
            reason = (
                f"{momentum_days}-day trend is positive; use volatility targeting "
                "to size the long exposure."
            )
        elif trend_return < 0:
            signal = "REDUCE"
            target_quote_notional = Decimal("0.00")
            reason = (
                f"{momentum_days}-day trend is negative; stay defensive or reduce "
                "spot exposure."
            )
        else:
            signal = "HOLD"
            target_quote_notional = Decimal("0.00")
            reason = "Trend is flat; no new exposure is suggested."

        return VolatilityTargetedTrendPlan(
            product_id=product_id,
            signal=signal,
            latest_close=latest_close,
            trend_return=trend_return.quantize(Decimal("0.0001")),
            realized_annual_volatility=realized_vol.quantize(Decimal("0.0001")),
            target_annual_volatility=target_vol,
            exposure_fraction=exposure_fraction.quantize(Decimal("0.0001")),
            max_quote_budget=max_quote_budget,
            target_quote_notional=target_quote_notional,
            candles_used=len(closes),
            lookback_days=lookback_days,
            momentum_days=momentum_days,
            reason=reason,
        )

    def _fetch_daily_candles(
        self,
        product_id: str,
        lookback_days: int,
        now: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        end = now or datetime.now(timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        start = end - timedelta(days=lookback_days + 1)

        response = self.rest_client.get_public_candles(
            product_id=product_id,
            start=str(int(start.timestamp())),
            end=str(int(end.timestamp())),
            granularity=self.DAILY_GRANULARITY,
            limit=lookback_days + 1,
        )
        response_dict = response_to_dict(response)
        candles = (
            response_dict.get("candles")
            if isinstance(response_dict, dict)
            else None
        )
        if not candles:
            raise ValueError(f"Coinbase returned no candles for {product_id}")

        return sorted(candles, key=lambda candle: int(candle.get("start", 0)))

    def _annualized_volatility(self, closes: List[Decimal]) -> Decimal:
        returns = []
        for index in range(1, len(closes)):
            previous_close = closes[index - 1]
            current_close = closes[index]
            if previous_close <= 0 or current_close <= 0:
                raise ValueError("Candle closes must be greater than 0")
            returns.append(float((current_close / previous_close) - Decimal("1")))

        if not returns:
            return Decimal("0")

        daily_vol = Decimal(str(pstdev(returns)))
        return daily_vol * Decimal(str(sqrt(float(self.ANNUALIZATION_DAYS))))

    def _target_exposure_fraction(
        self,
        target_vol: Decimal,
        realized_vol: Decimal,
        max_exposure: Decimal,
    ) -> Decimal:
        if realized_vol <= 0:
            return max_exposure

        return min(max_exposure, target_vol / realized_vol)
