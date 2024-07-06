import uuid
from decimal import Decimal, ROUND_HALF_UP


def calculate_base_size(
    fiat_amount: Decimal,
    spot_price: Decimal,
    base_increment: Decimal
) -> Decimal:
    """
    Calculate the base size for an order.

    Args:
        fiat_amount (Decimal): The amount in fiat currency.
        spot_price (Decimal): The current spot price.
        base_increment (Decimal): The base increment for the product.

    Returns:
        Decimal: The calculated base size.
    """
    return (fiat_amount / spot_price).quantize(
        base_increment, rounding=ROUND_HALF_UP
    )


def generate_client_order_id() -> str:
    """
    Generate a unique client order ID.

    Returns:
        str: A unique UUID string.
    """
    return str(uuid.uuid4())