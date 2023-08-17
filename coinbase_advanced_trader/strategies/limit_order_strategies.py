from decimal import Decimal, ROUND_HALF_UP
from .utils import get_spot_price
from coinbase_advanced_trader.cb_auth import CBAuth
from coinbase_advanced_trader.config import BUY_PRICE_MULTIPLIER, SELL_PRICE_MULTIPLIER
from coinbase_advanced_trader.coinbase_client import createOrder, generate_client_order_id, Side, Method, getProduct

# Initialize the single instance of CBAuth
cb_auth = CBAuth()


def fiat_limit_buy(product_id, fiat_amount, price_multiplier=BUY_PRICE_MULTIPLIER):
    """
    Place a limit buy order.

    :param product_id: The ID of the product to buy (e.g., "BTC-USD").
    :param fiat_amount: The amount in USD or other fiat to spend on buying (ie. $200).
    :param price_multiplier: Multiplier to apply to the current spot price to get the limit price.
    :return: Response of the order details.
    """
    # Coinbase maker fee rate
    maker_fee_rate = Decimal('0.004')

    # Fetch product details to get the quote_increment and base_increment
    product_details = getProduct(product_id)
    quote_increment = Decimal(product_details['quote_increment'])
    base_increment = Decimal(product_details['base_increment'])

    # Fetch the current spot price for the product
    spot_price = get_spot_price(product_id)

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

    # Create order configuration
    order_configuration = {
        'limit_price': str(limit_price),
        'base_size': str(base_size),
        'post_only': True
    }

    # Send the order
    order_details = createOrder(
        client_order_id=generate_client_order_id(),
        product_id=product_id,
        side=Side.BUY.name,
        order_type='limit_limit_gtc',
        order_configuration=order_configuration
    )

    return order_details


def fiat_limit_sell(product_id, fiat_amount, price_multiplier=SELL_PRICE_MULTIPLIER):
    """
    Place a limit sell order.

    :param product_id: The ID of the product to sell (e.g., "BTC-USD").
    :param fiat_amount: The amount in USD or other fiat to receive from selling (ie. $200).
    :param price_multiplier: Multiplier to apply to the current spot price to get the limit price.
    :return: Response of the order details.
    """
    # Coinbase maker fee rate
    maker_fee_rate = Decimal('0.004')

    # Fetch product details to get the quote_increment and base_increment
    product_details = getProduct(product_id)
    quote_increment = Decimal(product_details['quote_increment'])
    base_increment = Decimal(product_details['base_increment'])

    # Fetch the current spot price for the product
    spot_price = get_spot_price(product_id)

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

    # Create order configuration
    order_configuration = {
        'limit_price': str(limit_price),
        'base_size': str(base_size),
        'post_only': True
    }

    # Send the order
    order_details = createOrder(
        client_order_id=generate_client_order_id(),
        product_id=product_id,
        side=Side.SELL.name,
        order_type='limit_limit_gtc',
        order_configuration=order_configuration
    )

    return order_details
