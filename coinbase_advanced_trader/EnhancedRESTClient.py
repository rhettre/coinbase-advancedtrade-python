import uuid
from coinbase.rest import RESTClient
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

class Side(Enum):
    BUY = 1
    SELL = 0

class EnhancedRESTClient(RESTClient):
    def __init__(self, api_key, api_secret, **kwargs):
        super().__init__(api_key=api_key, api_secret=api_secret, **kwargs)

    def generate_client_order_id(self):
        return str(uuid.uuid4())

    def get_spot_price(self, product_id):
        """
        Fetches the current spot price of a specified product.

        Args:
            product_id (str): The ID of the product (e.g., "BTC-USD").

        Returns:
            float: The spot price as a float, or None if an error occurs.
        """
        try:
            response = self.get_product(product_id)
            # print("Response:", response)  # Log the entire response for debugging
            quote_increment = Decimal(response['quote_increment'])

            # Check whether the 'price' field exists in the response and return it as a float
            if 'price' in response:
                price = Decimal(response['price'])
                # Round the price to quote_increment number of digits
                rounded_price = price.quantize(quote_increment)
                return rounded_price
            else:
                # Print a specific error message if the 'price' field is missing
                print(f"'price' field missing in response for {product_id}")
                return None

        except Exception as e:
            print(f"Error fetching spot price for {product_id}: {e}")
            return None

    def calculate_base_size(self, fiat_amount, spot_price, base_increment):
        print(fiat_amount)
        fiat_amount_decimal = Decimal(fiat_amount)
        base_size = (fiat_amount_decimal / Decimal(spot_price) / Decimal(base_increment)).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP) * Decimal(base_increment)
        print(base_size)
        return str(base_size)

    def fiat_market_buy(self, product_id, fiat_amount):
        #Example: client.fiat_market_buy("BTC-USDC","10")
        order = self.market_order_buy(self.generate_client_order_id(), product_id, fiat_amount)
        if order['success']:
            print(f"Successfully placed a buy order for {fiat_amount} {product_id.split('-')[1]} of {product_id.split('-')[0]}.")
        else:
            failure_reason = order.get('failure_reason', '')
            preview_failure_reason = order.get(
                'error_response', {}).get('preview_failure_reason', '')
            print(
                f"Failed to place a buy order. Reason: {failure_reason}. Preview failure reason: {preview_failure_reason}")

        print("Coinbase response:", order)
        return order

    def fiat_market_sell(self, product_id, fiat_amount):
        #Example: client.fiat_market_sell("BTC-USDC","10")
        base_size = self.calculate_base_size(fiat_amount, self.get_spot_price(product_id), self.get_product(product_id)['base_increment'])
        order = self.market_order_sell(self.generate_client_order_id(), product_id, base_size)
        if order['success']:
            print(f"Successfully placed a sell order for {fiat_amount} {product_id.split('-')[1]} of {product_id.split('-')[0]}.")
        else:
            failure_reason = order.get('failure_reason', '')
            preview_failure_reason = order.get(
                'error_response', {}).get('preview_failure_reason', '')
            print(
                f"Failed to place a sell order. Reason: {failure_reason}. Preview failure reason: {preview_failure_reason}")

        print("Coinbase response:", order)
        return order





   