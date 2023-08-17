from coinbase_advanced_trader.cb_auth import CBAuth
import coinbase_advanced_trader.coinbase_client as client

# Get the singleton instance of CBAuth
cb_auth = CBAuth()


def get_spot_price(product_id):
    """
    Fetch the current spot price of a specified product.

    :param product_id: The ID of the product (e.g., "BTC-USD").
    :return: The spot price as a float, or None if an error occurs.
    """
    try:
        response = client.getProduct(product_id)
        # print("Response:", response)  # Log the entire response for debugging

        # Check whether the 'price' field exists in the response and return it as a float
        if 'price' in response:
            return float(response['price'])
        else:
            # Print a specific error message if the 'price' field is missing
            print(f"'price' field missing in response for {product_id}")
            return None

    except Exception as e:
        print(f"Error fetching spot price for {product_id}: {e}")
        return None
