from decimal import Decimal
from typing import Dict, Any, Optional

from coinbase.rest import RESTClient

from coinbase_advanced_trader.logger import logger


class PriceService:
    """Service for handling price-related operations."""

    def __init__(self, rest_client: RESTClient):
        """
        Initialize the PriceService.

        Args:
            rest_client (RESTClient): The REST client for API calls.
        """
        self.rest_client = rest_client

    def get_spot_price(self, product_id: str) -> Optional[Decimal]:
        """
        Get the spot price for a given product.

        Args:
            product_id (str): The ID of the product.

        Returns:
            Optional[Decimal]: The spot price, or None if an error occurs.
        """
        try:
            response = self.rest_client.get_product(product_id)
            quote_increment = Decimal(response['quote_increment'])

            if 'price' in response:
                price = Decimal(response['price'])
                return price.quantize(quote_increment)

            logger.error(f"'price' field missing in response for {product_id}")
            return None

        except Exception as e:
            logger.error(f"Error fetching spot price for {product_id}: {e}")
            return None

    def get_product_details(self, product_id: str) -> Dict[str, Decimal]:
        """
        Get the details of a product.

        Args:
            product_id (str): The ID of the product.

        Returns:
            Dict[str, Decimal]: A dictionary containing base and quote increments.
        """
        response = self.rest_client.get_product(product_id)
        return {
            'base_increment': Decimal(response['base_increment']),
            'quote_increment': Decimal(response['quote_increment'])
        }
