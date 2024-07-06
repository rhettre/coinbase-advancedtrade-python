from decimal import Decimal, ROUND_HALF_UP
from coinbase_advanced_trader.legacy.cb_auth import CBAuth
from .utils import get_spot_price
from coinbase_advanced_trader.legacy.coinbase_client import createOrder, generate_client_order_id, Side, getProduct

cb_auth = CBAuth()


def calculate_base_size(fiat_amount, spot_price, base_increment):
    base_size = (fiat_amount / spot_price / base_increment).quantize(
        Decimal('1'), rounding=ROUND_HALF_UP) * base_increment
    return base_size


def _market_order(product_id, fiat_amount, side):
    product_details = getProduct(product_id)
    base_increment = Decimal(product_details['base_increment'])
    spot_price = get_spot_price(product_id)

    if side == Side.SELL.name:
        base_size = calculate_base_size(
            fiat_amount, spot_price, base_increment)
        order_configuration = {'base_size': str(base_size)}
    else:
        order_configuration = {'quote_size': str(fiat_amount)}

    order_details = createOrder(
        client_order_id=generate_client_order_id(),
        product_id=product_id,
        side=side,
        order_type='market_market_ioc',
        order_configuration=order_configuration
    )

    if order_details['success']:
        print(
            f"Successfully placed a {side} order for {fiat_amount} USD of {product_id.split('-')[0]}.")
    else:
        failure_reason = order_details.get('failure_reason', '')
        preview_failure_reason = order_details.get(
            'error_response', {}).get('preview_failure_reason', '')
        print(
            f"Failed to place a {side} order. Reason: {failure_reason}. Preview failure reason: {preview_failure_reason}")

    print("Coinbase response:", order_details)

    return order_details


def fiat_market_buy(product_id, fiat_amount):
    return _market_order(product_id, fiat_amount, Side.BUY.name)


def fiat_market_sell(product_id, fiat_amount):
    return _market_order(product_id, fiat_amount, Side.SELL.name)
