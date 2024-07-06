from abc import ABC, abstractmethod
from typing import Optional

from coinbase_advanced_trader.models import Order
from .order_service import OrderService
from .price_service import PriceService


class BaseTradingStrategy(ABC):
    """
    Abstract base class for trading strategies.

    This class provides a common interface for all trading strategies,
    including access to order and price services.
    """

    def __init__(
        self,
        order_service: OrderService,
        price_service: PriceService
    ) -> None:
        """
        Initialize the trading strategy.

        Args:
            order_service (OrderService): Service for handling orders.
            price_service (PriceService): Service for handling price-related operations.
        """
        self.order_service = order_service
        self.price_service = price_service

    @abstractmethod
    def execute_trade(self, product_id: str, fiat_amount: str) -> Optional[Order]:
        """
        Execute a trade based on the strategy.

        Args:
            product_id (str): The ID of the product to trade.
            fiat_amount (str): The amount of fiat currency to trade.

        Returns:
            Optional[Order]: The executed order, or None if the trade failed.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement execute_trade method")