from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"

@dataclass
class Order:
    id: str
    product_id: str
    side: OrderSide
    type: OrderType
    size: Decimal
    price: Optional[Decimal] = None
    client_order_id: Optional[str] = None
    status: str = "pending"

    def __post_init__(self):
        if self.type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders must have a price")

    @property
    def is_buy(self) -> bool:
        return self.side == OrderSide.BUY

    @property
    def is_sell(self) -> bool:
        return self.side == OrderSide.SELL

    @property
    def is_market(self) -> bool:
        return self.type == OrderType.MARKET

    @property
    def is_limit(self) -> bool:
        return self.type == OrderType.LIMIT