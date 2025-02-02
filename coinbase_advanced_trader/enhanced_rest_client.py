"""Enhanced REST client for Coinbase Advanced Trading API.

This module provides additional trading functionalities on top of the base RESTClient.
All Coinbase v2 API interactions (signing, URL parsing, and requests) are encapsulated
here and used by various service methods.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from coinbase.rest import RESTClient

from .services.order_service import OrderService
from .services.fear_and_greed_strategy import FearAndGreedStrategy
from .services.price_service import PriceService
from .trading_config import FearAndGreedConfig
from coinbase_advanced_trader.constants import DEFAULT_CONFIG
from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.services.account_service import AccountService, Account
from coinbase_advanced_trader.services.funds_service import FundsService


class EnhancedRESTClient(RESTClient):
    """Enhanced REST client with additional trading functionalities."""

    def __init__(self, api_key: str, api_secret: str, **kwargs: Any) -> None:
        """
        Initialize the EnhancedRESTClient with trading service dependencies.

        Args:
            api_key: The API key for authentication.
            api_secret: The API secret for authentication.
            **kwargs: Additional keyword arguments for RESTClient.
        """
        super().__init__(api_key=api_key, api_secret=api_secret, **kwargs)

        # Initialize service dependencies
        self._account_service = AccountService(self)
        self._funds_service = FundsService(self)
        self._price_service = PriceService(self)
        self._order_service = OrderService(self, self._price_service)
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
        price_multiplier: float = DEFAULT_CONFIG['BUY_PRICE_MULTIPLIER']
    ) -> Dict[str, Any]:
        """
        Execute a fiat limit buy order.

        Args:
            product_id: Coinbase product identifier.
            fiat_amount: Amount of fiat to spend.
            limit_price: Desired limit price (optional).
            price_multiplier: Multiplier used if no limit price is provided.

        Returns:
            The API response as a dict.
        """
        return self._order_service.fiat_limit_buy(
            product_id, fiat_amount, limit_price, price_multiplier
        )

    def fiat_limit_sell(
        self,
        product_id: str,
        fiat_amount: str,
        limit_price: Optional[str] = None,
        price_multiplier: float = DEFAULT_CONFIG['SELL_PRICE_MULTIPLIER']
    ) -> Dict[str, Any]:
        """
        Execute a fiat limit sell order.

        Args:
            product_id: Coinbase product identifier.
            fiat_amount: Amount of fiat to receive.
            limit_price: Desired limit price (optional).
            price_multiplier: Multiplier used if no limit price is provided.

        Returns:
            The API response as a dict.
        """
        return self._order_service.fiat_limit_sell(
            product_id, fiat_amount, limit_price, price_multiplier
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