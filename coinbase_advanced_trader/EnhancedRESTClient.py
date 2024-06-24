import uuid
from coinbase.rest import RESTClient
from coinbase_advanced_trader.config import BUY_PRICE_MULTIPLIER, SELL_PRICE_MULTIPLIER
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

    def fiat_limit_buy(self,product_id, fiat_amount, price_multiplier=BUY_PRICE_MULTIPLIER):
        """
        Places a limit buy order.

        Args:
            product_id (str): The ID of the product to buy (e.g., "BTC-USD").
            fiat_amount (float): The amount in USD or other fiat to spend on buying (ie. $200).
            price_multiplier (float, optional): Multiplier to apply to the current spot price to get the limit price. Defaults to BUY_PRICE_MULTIPLIER.

        Returns:
            dict: The response of the order details.
        """
        # Coinbase maker fee rate
        maker_fee_rate = Decimal('0.004')

        # Fetch product details to get the quote_increment and base_increment
        product_details = self.get_product(product_id)
        quote_increment = Decimal(product_details['quote_increment'])
        base_increment = Decimal(product_details['base_increment'])

        # Fetch the current spot price for the product
        spot_price = self.get_spot_price(product_id)

        # Calculate the limit price
        limit_price = Decimal(spot_price) * Decimal(price_multiplier)

        # Round the limit price to the appropriate number of decimal places
        limit_price = limit_price.quantize(quote_increment)

        # Adjust the fiat_amount for the maker fee
        effective_fiat_amount = Decimal(fiat_amount) * (1 - maker_fee_rate)

        # Calculate the equivalent amount in the base currency (e.g., BTC) for the given USD amount
        base_size = effective_fiat_amount / limit_price

        # Round base_size to the nearest allowed increment
        base_size = (base_size / base_increment).quantize(Decimal('1'),
                                                        rounding=ROUND_HALF_UP) * base_increment

        order = self.limit_order_gtc_buy(self.generate_client_order_id(),product_id, str(base_size), str(limit_price))
        # Print a human-readable message
        if order['success']:
            base_size = Decimal(
                order['order_configuration']['limit_limit_gtc']['base_size'])
            limit_price = Decimal(
                order['order_configuration']['limit_limit_gtc']['limit_price'])
            total_amount = base_size * limit_price
            print(
                f"Successfully placed a limit buy order for {base_size} {product_id} (${total_amount:.2f}) at a price of {limit_price} USD.")
        else:
            print(
                f"Failed to place a limit buy order. Reason: {order['failure_reason']}")

        print("Coinbase response:", order)

        return order


    def fiat_limit_sell(self, product_id, fiat_amount, price_multiplier=SELL_PRICE_MULTIPLIER):
        """
        Places a limit sell order.

        Args:
            product_id (str): The ID of the product to sell (e.g., "BTC-USD").
            fiat_amount (float): The amount in USD or other fiat to receive from selling (ie. $200).
            price_multiplier (float, optional): Multiplier to apply to the current spot price to get the limit price. Defaults to SELL_PRICE_MULTIPLIER.

        Returns:
            dict: The response of the order details.
        """
        # Coinbase maker fee rate
        maker_fee_rate = Decimal('0.004')

        # Fetch product details to get the quote_increment and base_increment
        product_details = self.get_product(product_id)
        quote_increment = Decimal(product_details['quote_increment'])
        base_increment = Decimal(product_details['base_increment'])

        # Fetch the current spot price for the product
        spot_price = self.get_spot_price(product_id)

        # Calculate the limit price
        limit_price = Decimal(spot_price) * Decimal(price_multiplier)

        # Round the limit price to the appropriate number of decimal places
        limit_price = limit_price.quantize(quote_increment)

        # Adjust the fiat_amount for the maker fee
        effective_fiat_amount = Decimal(fiat_amount) / (1 - maker_fee_rate)

        # Calculate the equivalent amount in the base currency (e.g., BTC) for the given USD amount
        base_size = effective_fiat_amount / limit_price

        # Round base_size to the nearest allowed increment
        base_size = (base_size / base_increment).quantize(Decimal('1'),
                                                        rounding=ROUND_HALF_UP) * base_increment

        order = self.limit_order_gtc_sell(self.generate_client_order_id(),product_id, str(base_size), str(limit_price))

        # Print a human-readable message
        if order['success']:
            base_size = Decimal(
                order['order_configuration']['limit_limit_gtc']['base_size'])
            limit_price = Decimal(
                order['order_configuration']['limit_limit_gtc']['limit_price'])
            total_amount = base_size * limit_price
            print(
                f"Successfully placed a limit sell order for {base_size} {product_id} (${total_amount:.2f}) at a price of {limit_price} USD.")
        else:
            print(
                f"Failed to place a limit sell order. Reason: {order['failure_reason']}")

        print("Coinbase response:", order)

        return order


   