from coinbase_advanced_trader.legacy.cb_auth import CBAuth
import coinbase_advanced_trader.legacy.coinbase_client as client
from decimal import Decimal

# Get the singleton instance of CBAuth
cb_auth = CBAuth()


def get_spot_price(product_id):
    """
    Fetches the current spot price of a specified product.

    Args:
        product_id (str): The ID of the product (e.g., "BTC-USD").

    Returns:
        float: The spot price as a float, or None if an error occurs.
    """
    try:
        response = client.getProduct(product_id)
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
