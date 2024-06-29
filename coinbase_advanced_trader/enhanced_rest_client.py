"""Enhanced REST client for Coinbase Advanced Trading API."""

from typing import Optional
from coinbase.rest import RESTClient
from .services.order_service import OrderService
from .services.trading_strategy_service import TradingStrategyService
from .services.price_service import PriceService
from coinbase_advanced_trader.config import BUY_PRICE_MULTIPLIER, SELL_PRICE_MULTIPLIER


class EnhancedRESTClient(RESTClient):
    """Enhanced REST client with additional trading functionalities."""

    def __init__(self, api_key: str, api_secret: str, **kwargs):
        """
        Initialize the EnhancedRESTClient.

        Args:
            api_key (str): The API key for authentication.
            api_secret (str): The API secret for authentication.
            **kwargs: Additional keyword arguments for RESTClient.
        """
        super().__init__(api_key=api_key, api_secret=api_secret, **kwargs)
        self._price_service = PriceService(self)
        self._order_service = OrderService(self, self._price_service)
        self._trading_strategy_service = TradingStrategyService(
            self._order_service, self._price_service
        )

    def fiat_market_buy(self, product_id: str, fiat_amount: str):
        """
        Place a market buy order with fiat currency.

        Args:
            product_id (str): The product identifier.
            fiat_amount (str): The amount of fiat currency to spend.

        Returns:
            The result of the market buy order.
        """
        return self._order_service.fiat_market_buy(product_id, fiat_amount)

    def fiat_market_sell(self, product_id: str, fiat_amount: str):
        """
        Place a market sell order with fiat currency.

        Args:
            product_id (str): The product identifier.
            fiat_amount (str): The amount of fiat currency to receive.

        Returns:
            The result of the market sell order.
        """
        return self._order_service.fiat_market_sell(product_id, fiat_amount)

    def fiat_limit_buy(
        self,
        product_id: str,
        fiat_amount: str,
        price_multiplier: float = BUY_PRICE_MULTIPLIER
    ):
        """
        Place a limit buy order with fiat currency.

        Args:
            product_id (str): The product identifier.
            fiat_amount (str): The amount of fiat currency to spend.
            price_multiplier (float): The price multiplier for the limit order.

        Returns:
            The result of the limit buy order.
        """
        return self._order_service.fiat_limit_buy(
            product_id, fiat_amount, price_multiplier
        )

    def fiat_limit_sell(
        self,
        product_id: str,
        fiat_amount: str,
        price_multiplier: float = SELL_PRICE_MULTIPLIER
    ):
        """
        Place a limit sell order with fiat currency.

        Args:
            product_id (str): The product identifier.
            fiat_amount (str): The amount of fiat currency to receive.
            price_multiplier (float): The price multiplier for the limit order.

        Returns:
            The result of the limit sell order.
        """
        return self._order_service.fiat_limit_sell(
            product_id, fiat_amount, price_multiplier
        )

    def trade_based_on_fgi(
        self,
        product_id: str,
        fiat_amount: str,
        schedule: Optional[str] = None
    ):
        """
        Execute a complex trade based on the Fear and Greed Index.

        Args:
            product_id (str): The product identifier.
            fiat_amount (float): The amount of fiat currency to trade.
            schedule (Optional[str]): The trading schedule, if any.

        Returns:
            The result of the trade execution.
        """
        return self._trading_strategy_service.trade_based_on_fgi(
            product_id, fiat_amount, schedule
        )
