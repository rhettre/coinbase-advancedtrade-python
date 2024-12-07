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
            The current spot price as a Decimal, or None if price cannot be retrieved.
        """
        try:
            response = self.rest_client.get_product(product_id)
            
            # Convert response to dictionary if it's a GetProductResponse object
            response_dict = response if isinstance(response, dict) else response.__dict__
            
            if 'price' not in response_dict or 'quote_increment' not in response_dict:
                logger.error(f"Required fields missing in response for {product_id}")
                return None

            price = Decimal(response_dict['price'])
            quote_increment = Decimal(response_dict['quote_increment'])
            return price.quantize(quote_increment)

        except Exception as e:
            logger.error(f"Error fetching spot price for {product_id}: {e}")
            return None

    def get_product_details(self, product_id: str) -> Optional[Dict[str, Decimal]]:
        """
        Get the details of a product.

        Args:
            product_id (str): The ID of the product.

        Returns:
            Optional[Dict[str, Decimal]]: A dictionary containing base and quote increments, or None if failed.
        """
        try:
            response = self.rest_client.get_product(product_id)
            return {
                'base_increment': Decimal(response['base_increment']),
                'quote_increment': Decimal(response['quote_increment'])
            }
        except Exception as e:
            logger.error(f"Error fetching product details for {product_id}: {e}")
            return None
