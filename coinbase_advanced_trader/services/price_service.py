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
            logger.info(f"Starting spot price fetch for {product_id}")
            
            # Add timeout to prevent hanging
            response = self.rest_client.get_product(product_id, timeout=10)
            
            # Log the entire response for debugging
            logger.info(f"Raw response from Coinbase: {response}")
            
            if not response:
                logger.error(f"Empty response received for {product_id}")
                return None
            
            # Convert response to dictionary if it's a GetProductResponse object
            response_dict = response if isinstance(response, dict) else response.__dict__
            
            if 'quote_increment' not in response_dict:
                logger.error(f"'quote_increment' missing in response for {product_id}")
                return None
            
            quote_increment = Decimal(response_dict['quote_increment'])
            logger.info(f"Quote increment: {quote_increment}")

            if 'price' not in response_dict:
                logger.error(f"'price' field missing in response for {product_id}")
                return None

            price = Decimal(response_dict['price'])
            final_price = price.quantize(quote_increment)
            logger.info(f"Final calculated price for {product_id}: {final_price}")
            return final_price

        except TimeoutError:
            logger.error(f"Timeout while fetching spot price for {product_id}")
            return None
        except ConnectionError as e:
            logger.error(f"Connection error while fetching spot price for {product_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching spot price for {product_id}: {e}")
            logger.error(f"Error type: {type(e)}")
            return None

    def get_product_details(self, product_id: str, timeout: int = 5) -> Optional[Dict[str, Decimal]]:
        """
        Get the details of a product.

        Args:
            product_id (str): The ID of the product.
            timeout (int): Timeout in seconds for the API call.

        Returns:
            Optional[Dict[str, Decimal]]: A dictionary containing base and quote increments, or None if failed.
        """
        try:
            response = self.rest_client.get_product(product_id, timeout=timeout)
            return {
                'base_increment': Decimal(response['base_increment']),
                'quote_increment': Decimal(response['quote_increment'])
            }
        except Exception as e:
            logger.error(f"Error fetching product details for {product_id}: {e}")
            return None
