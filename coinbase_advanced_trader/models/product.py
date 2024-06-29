from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Product:
    id: str
    base_currency: str
    quote_currency: str
    base_increment: Decimal
    quote_increment: Decimal
    min_market_funds: Decimal
    max_market_funds: Decimal
    status: str
    trading_disabled: bool

    @property
    def name(self) -> str:
        return f"{self.base_currency}-{self.quote_currency}"

    def __str__(self) -> str:
        return f"Product({self.name})"