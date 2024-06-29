from decimal import Decimal
from typing import Dict, Any
from coinbase.rest import RESTClient
from coinbase_advanced_trader.logger import logger

class PriceService:
    def __init__(self, rest_client: RESTClient):
        self.rest_client = rest_client

    def get_spot_price(self, product_id: str) -> Decimal:
        try:
            response = self.rest_client.get_product(product_id)
            quote_increment = Decimal(response['quote_increment'])

            if 'price' in response:
                price = Decimal(response['price'])
                return price.quantize(quote_increment)
            else:
                logger.error(f"'price' field missing in response for {product_id}")
                return None

        except Exception as e:
            logger.error(f"Error fetching spot price for {product_id}: {e}")
            return None

    def get_product_details(self, product_id: str) -> Dict[str, Any]:
        response = self.rest_client.get_product(product_id)
        return {
            'base_increment': Decimal(response['base_increment']),
            'quote_increment': Decimal(response['quote_increment'])
        }
