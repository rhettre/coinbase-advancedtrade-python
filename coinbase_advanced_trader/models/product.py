from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Product:
    """
    Represents a trading product with its associated attributes.

    Attributes:
        id (str): Unique identifier for the product.
        base_currency (str): The base currency of the product.
        quote_currency (str): The quote currency of the product.
        base_increment (Decimal): Minimum increment for the base currency.
        quote_increment (Decimal): Minimum increment for the quote currency.
        min_market_funds (Decimal): Minimum funds required for market orders.
        max_market_funds (Decimal): Maximum funds allowed for market orders.
        status (str): Current status of the product.
        trading_disabled (bool): Whether trading is currently disabled.
    """

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
        """
        Returns the product name in the format 'base_currency-quote_currency'.

        Returns:
            str: The product name.
        """
        return f"{self.base_currency}-{self.quote_currency}"

    def __str__(self) -> str:
        """
        Returns a string representation of the Product.

        Returns:
            str: A string representation of the Product.
        """
        return f"Product({self.name})"