from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


class OrderSide(Enum):
    """Enum representing the side of an order (buy or sell)."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Enum representing the type of an order (market or limit)."""
    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Order:
    """
    Represents an order in the trading system.

    Attributes:
        id (str): Unique identifier for the order.
        product_id (str): Identifier for the product being traded.
        side (OrderSide): Whether the order is a buy or sell.
        type (OrderType): Whether the order is a market or limit order.
        size (Decimal): The size of the order.
        price (Optional[Decimal]): The price for limit orders (None for market orders).
        client_order_id (Optional[str]): Client-specified order ID.
        status (str): Current status of the order.
    """

    id: str
    product_id: str
    side: OrderSide
    type: OrderType
    size: Decimal
    price: Optional[Decimal] = None
    client_order_id: Optional[str] = None
    status: str = "pending"

    def __post_init__(self):
        """Validates that limit orders have a price."""
        if self.type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders must have a price")

    @property
    def is_buy(self) -> bool:
        """Returns True if the order is a buy order."""
        return self.side == OrderSide.BUY

    @property
    def is_sell(self) -> bool:
        """Returns True if the order is a sell order."""
        return self.side == OrderSide.SELL

    @property
    def is_market(self) -> bool:
        """Returns True if the order is a market order."""
        return self.type == OrderType.MARKET

    @property
    def is_limit(self) -> bool:
        """Returns True if the order is a limit order."""
        return self.type == OrderType.LIMIT