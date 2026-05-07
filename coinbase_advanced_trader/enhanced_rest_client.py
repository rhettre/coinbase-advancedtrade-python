"""Enhanced REST client for Coinbase Advanced Trading API.

This module provides additional trading functionalities on top of the base RESTClient.
All Coinbase v2 API interactions (signing, URL parsing, and requests) are encapsulated
here and used by various service methods.
"""

import os
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from coinbase.constants import API_ENV_KEY, API_SECRET_ENV_KEY
from coinbase.rest import RESTClient

from .services.order_service import OrderService
from .services.fear_and_greed_strategy import FearAndGreedStrategy
from .services.price_service import PriceService
from .services.strategy_planner_service import (
    StrategyPlannerService,
    VolatilityTargetedTrendPlan,
)
from .services.websocket_service import OrderEvent, TickerUpdate, WebsocketService
from .trading_config import FearAndGreedConfig
from coinbase_advanced_trader.constants import DEFAULT_CONFIG
from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.services.account_service import AccountService, Account
from coinbase_advanced_trader.services.funds_service import FundsService


class EnhancedRESTClient(RESTClient):
    """Enhanced REST client with additional trading functionalities."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the EnhancedRESTClient with trading service dependencies.

        Args:
            api_key: The API key for authentication. Defaults to COINBASE_API_KEY.
            api_secret: The API secret for authentication. Defaults to COINBASE_API_SECRET.
            **kwargs: Additional keyword arguments for RESTClient.
        """
        api_key = api_key or os.getenv(API_ENV_KEY)
        api_secret = api_secret or os.getenv(API_SECRET_ENV_KEY)
        super().__init__(api_key=api_key, api_secret=api_secret, **kwargs)

        # Initialize service dependencies
        self._account_service = AccountService(self)
        self._funds_service = FundsService(self)
        self._price_service = PriceService(self)
        self._order_service = OrderService(self, self._price_service)
        self._websocket_service = WebsocketService(self)
        self._strategy_planner_service = StrategyPlannerService(self)
        self._config = FearAndGreedConfig()
        self._fear_and_greed_strategy = FearAndGreedStrategy(
            self._order_service, self._price_service, self._config
        )

    # -------------------------------------------------------------------------
    # Account Services
    # -------------------------------------------------------------------------
    def get_crypto_balance(self, currency: str) -> Decimal:
        """
        Get the available balance of a specific cryptocurrency.

        Args:
            currency: The currency code (e.g., 'BTC', 'ETH', 'USDC').

        Returns:
            The available balance as a Decimal.
        """
        return self._account_service.get_crypto_balance(currency)

    def list_held_crypto_balances(self) -> Dict[str, Decimal]:
        """
        Get a dictionary of held cryptocurrencies and their respective balances.

        Returns:
            A dict mapping currency codes to their balances.
        """
        return self._account_service.list_held_crypto_balances()

    # -------------------------------------------------------------------------
    # Fear and Greed Index Trading Configuration
    # -------------------------------------------------------------------------
    def update_fgi_schedule(self, new_schedule: List[Dict[str, Any]]) -> bool:
        """
        Update the Fear and Greed Index (FGI) trading schedule.

        Args:
            new_schedule: List of configuration dictionaries for trading rules.

        Returns:
            True if successfully updated; False otherwise.

        Raises:
            ValueError: If the provided schedule is invalid.
        """
        if not self._config.validate_schedule(new_schedule):
            logger.warning("Invalid FGI schedule provided. Update rejected.")
            return False

        try:
            self._config.update_fgi_schedule(new_schedule)
            logger.info("FGI schedule successfully updated.")
            return True
        except ValueError as error:
            logger.error(f"Failed to update FGI schedule: {error}")
            raise

    def get_fgi_schedule(self) -> List[Dict[str, Any]]:
        """
        Retrieve the current Fear and Greed Index schedule.

        Returns:
            The FGI schedule as a list of dictionaries.
        """
        return self._config.get_fgi_schedule()

    def validate_fgi_schedule(self, schedule: List[Dict[str, Any]]) -> bool:
        """
        Validate an FGI trading schedule without applying it.

        Args:
            schedule: The schedule to validate.

        Returns:
            True if the schedule is valid; False otherwise.
        """
        return self._config.validate_schedule(schedule)

    # -------------------------------------------------------------------------
    # Fiat Trading (Market and Limit Orders)
    # -------------------------------------------------------------------------
    def fiat_market_buy(self, product_id: str, fiat_amount: str) -> Dict[str, Any]:
        """
        Execute a fiat market buy order.

        Args:
            product_id: Coinbase product identifier.
            fiat_amount: Amount of fiat to spend.

        Returns:
            The API response as a dict.
        """
        return self._order_service.fiat_market_buy(product_id, fiat_amount)

    def fiat_market_sell(self, product_id: str, fiat_amount: str) -> Dict[str, Any]:
        """
        Execute a fiat market sell order.

        Args:
            product_id: Coinbase product identifier.
            fiat_amount: Amount of fiat to receive.

        Returns:
            The API response as a dict.
        """
        return self._order_service.fiat_market_sell(product_id, fiat_amount)

    def fiat_limit_buy(
        self,
        product_id: str,
        fiat_amount: str,
        limit_price: Optional[str] = None,
        price_multiplier: float = DEFAULT_CONFIG['BUY_PRICE_MULTIPLIER'],
        post_only: bool = DEFAULT_CONFIG['POST_ONLY_DEFAULT']
    ) -> Dict[str, Any]:
        """
        Execute a fiat limit buy order.

        Args:
            product_id: Coinbase product identifier.
            fiat_amount: Amount of fiat to spend.
            limit_price: Desired limit price (optional).
            price_multiplier: Multiplier used if no limit price is provided.
            post_only: Whether the order should be post-only (maker only).

        Returns:
            The API response as a dict.
        """
        return self._order_service.fiat_limit_buy(
            product_id, fiat_amount, limit_price, price_multiplier, post_only
        )

    def fiat_limit_sell(
        self,
        product_id: str,
        fiat_amount: str,
        limit_price: Optional[str] = None,
        price_multiplier: float = DEFAULT_CONFIG['SELL_PRICE_MULTIPLIER'],
        post_only: bool = DEFAULT_CONFIG['POST_ONLY_DEFAULT']
    ) -> Dict[str, Any]:
        """
        Execute a fiat limit sell order.

        Args:
            product_id: Coinbase product identifier.
            fiat_amount: Amount of fiat to receive.
            limit_price: Desired limit price (optional).
            price_multiplier: Multiplier used if no limit price is provided.
            post_only: Whether the order should be post-only (maker only).

        Returns:
            The API response as a dict.
        """
        return self._order_service.fiat_limit_sell(
            product_id, fiat_amount, limit_price, price_multiplier, post_only
        )

    def limit_sell_base_size(
        self,
        product_id: str,
        base_size: str,
        limit_price: str,
        post_only: bool = DEFAULT_CONFIG['POST_ONLY_DEFAULT']
    ) -> Any:
        """
        Place a limit sell order for an exact base asset quantity.

        This is the safer follow-up helper for WebSocket fill workflows, where
        Coinbase reports the actual filled base size.
        """
        return self._order_service.limit_sell_base_size(
            product_id, base_size, limit_price, post_only
        )

    def cancel_open_orders(
        self,
        product_id: Optional[str] = None,
        side: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Cancel open orders, optionally filtered by product_id and side.

        Args:
            product_id: Optional product filter, like "BTC-USDC".
            side: Optional side filter, either "BUY", "SELL", OrderSide.BUY, or OrderSide.SELL.
        """
        return self._order_service.cancel_open_orders(product_id, side)

    # -------------------------------------------------------------------------
    # WebSocket Workflows
    # -------------------------------------------------------------------------
    def watch_ticker(
        self,
        product_ids: Union[str, Sequence[str]],
        seconds: int = 10,
        callback: Optional[Callable[[TickerUpdate], None]] = None,
        print_prices: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> List[TickerUpdate]:
        """
        Watch live public ticker prices with no API key required.

        This intentionally wraps the business-friendly demo workflow, not every
        official WebSocket channel.
        """
        return self._websocket_service.watch_ticker(
            product_ids=product_ids,
            seconds=seconds,
            callback=callback,
            print_prices=print_prices,
            retry=retry,
            verbose=verbose,
        )

    def watch_prices(
        self,
        product_ids: Union[str, Sequence[str]],
        seconds: int = 10,
        callback: Optional[Callable[[TickerUpdate], None]] = None,
        print_prices: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> List[TickerUpdate]:
        """Alias for watch_ticker that reads nicely in tutorials."""
        return self.watch_ticker(
            product_ids=product_ids,
            seconds=seconds,
            callback=callback,
            print_prices=print_prices,
            retry=retry,
            verbose=verbose,
        )

    def watch_order_events(
        self,
        product_ids: Union[str, Sequence[str]],
        callback: Optional[Callable[[OrderEvent], None]] = None,
        seconds: Optional[int] = None,
        include_heartbeats: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> List[OrderEvent]:
        """
        Watch authenticated user-channel order events.

        Pass seconds for a bounded tutorial demo; omit it for a long-running bot.
        """
        return self._websocket_service.watch_order_events(
            product_ids=product_ids,
            callback=callback,
            seconds=seconds,
            include_heartbeats=include_heartbeats,
            retry=retry,
            verbose=verbose,
        )

    def wait_for_order_fill(
        self,
        order_id: str,
        product_id: Union[str, Sequence[str]],
        timeout: int = 300,
        callback: Optional[Callable[[OrderEvent], None]] = None,
        include_heartbeats: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> OrderEvent:
        """Wait for Coinbase to push a FILLED event for the given order."""
        return self._websocket_service.wait_for_order_fill(
            order_id=order_id,
            product_id=product_id,
            timeout=timeout,
            callback=callback,
            include_heartbeats=include_heartbeats,
            retry=retry,
            verbose=verbose,
        )

    def buy_then_limit_sell_on_fill(
        self,
        product_id: str,
        fiat_amount: str,
        sell_price_multiplier: str = "1.05",
        timeout: int = 300,
        post_only: bool = DEFAULT_CONFIG['POST_ONLY_DEFAULT'],
        callback: Optional[Callable[[OrderEvent], None]] = None,
    ) -> Dict[str, Any]:
        """
        Buy with fiat, wait for the real fill, then place a take-profit limit sell.

        This is a WebSocket business-case wrapper: no polling loop, and the sell
        order uses the actual filled size and average fill price Coinbase sends.
        """
        buy_order, fill = self._websocket_service.place_order_and_wait_for_fill(
            product_id=product_id,
            place_order=lambda: self.fiat_market_buy(product_id, fiat_amount),
            timeout=timeout,
            callback=callback,
        )

        if fill.filled_size <= 0:
            raise ValueError(f"Order {buy_order.id} filled without a positive base size.")
        if fill.average_filled_price <= 0:
            raise ValueError(f"Order {buy_order.id} filled without a usable average price.")

        sell_limit_price = fill.average_filled_price * Decimal(str(sell_price_multiplier))
        sell_order = self.limit_sell_base_size(
            product_id=product_id,
            base_size=str(fill.filled_size),
            limit_price=str(sell_limit_price),
            post_only=post_only,
        )

        return {
            "buy_order": buy_order,
            "fill": fill,
            "sell_order": sell_order,
            "sell_limit_price": sell_order.price,
        }

    # -------------------------------------------------------------------------
    # Risk-First Strategy Planning
    # -------------------------------------------------------------------------
    def build_volatility_targeted_trend_plan(
        self,
        product_id: str,
        quote_budget: str,
        lookback_days: int = 120,
        momentum_days: int = 30,
        target_annual_volatility: str = "0.08",
        max_exposure_fraction: str = "1",
    ) -> VolatilityTargetedTrendPlan:
        """
        Build a dry-run volatility-targeted trend plan from public daily candles.

        The plan does not place orders. It is meant for trader-friendly demos
        where REST computes a slower signal and WebSockets handle live fills.
        """
        return self._strategy_planner_service.build_volatility_targeted_trend_plan(
            product_id=product_id,
            quote_budget=quote_budget,
            lookback_days=lookback_days,
            momentum_days=momentum_days,
            target_annual_volatility=target_annual_volatility,
            max_exposure_fraction=max_exposure_fraction,
        )

    # -------------------------------------------------------------------------
    # Fear and Greed-Based Trade Execution
    # -------------------------------------------------------------------------
    def trade_based_on_fgi(
        self,
        product_id: str,
        fiat_amount: str,
        schedule: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Execute a trade based on the Fear and Greed Index strategy.

        Args:
            product_id: Coinbase product identifier.
            fiat_amount: Amount of fiat to trade.
            schedule: Optional trading schedule to override defaults.

        Returns:
            The API response as a dict.
        """
        return self._fear_and_greed_strategy.execute_trade(product_id, fiat_amount)

    # -------------------------------------------------------------------------
    # Funds Operations (Delegated to FundsService)
    # Note: The actual funds_service methods (deposit/withdraw)
    # are implemented in the FundsService module.
    # -------------------------------------------------------------------------
    def deposit_fiat(
        self,
        account_id: str,
        payment_method_id: str,
        amount: str,
        currency: str = "USD",
        commit: bool = True
    ) -> Dict[str, Any]:
        """
        Deposit fiat into a Coinbase fiat account.

        Args:
            account_id: Coinbase account identifier.
            payment_method_id: Payment method identifier.
            amount: Amount to deposit.
            currency: Currency code (default "USD").
            commit: Whether to commit immediately.

        Returns:
            The API response as a dict.
        """
        return self._funds_service.deposit_fiat(
            account_id, payment_method_id, amount, currency, commit
        )

    def show_deposit_methods(self) -> None:
        """Show all payment methods that allow deposits."""
        return self._account_service.show_deposit_methods()

    def get_account_by_currency(self, currency: str) -> Optional[Account]:
        """Show account details for a specific currency."""
        return self._account_service.get_account_by_currency(currency)
