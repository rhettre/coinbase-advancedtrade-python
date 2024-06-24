import uuid
from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from coinbase.rest import RESTClient
from coinbase_advanced_trader.config import BUY_PRICE_MULTIPLIER, SELL_PRICE_MULTIPLIER
from coinbase_advanced_trader.logger import logger

class Side(Enum):
    BUY = 1
    SELL = 0

class EnhancedRESTClient(RESTClient):
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        super().__init__(api_key=api_key, api_secret=api_secret, **kwargs)
        self.MAKER_FEE_RATE = Decimal('0.004')

    def _generate_client_order_id(self) -> str:
        return str(uuid.uuid4())

    def get_spot_price(self, product_id: str) -> Decimal:
        """
        Fetches the current spot price of a specified product.

        Args:
            product_id (str): The ID of the product (e.g., "BTC-USD").

        Returns:
            Decimal: The spot price as a Decimal, or None if an error occurs.
        """
        try:
            response = self.get_product(product_id)
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

    def _calculate_base_size(self, fiat_amount: Decimal, spot_price: Decimal, base_increment: Decimal) -> Decimal:
        return ((fiat_amount / spot_price) / base_increment).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * base_increment

    def fiat_market_buy(self, product_id: str, fiat_amount: str) -> Dict[str, Any]:
        """
        Place a market buy order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to buy (e.g., "BTC-USDC").
            fiat_amount (str): The amount of fiat currency to spend.

        Returns:
            dict: The order response from Coinbase.
        """
        order = self.market_order_buy(self._generate_client_order_id(), product_id, fiat_amount)
        self._log_order_result(order, product_id, fiat_amount, Side.BUY)
        return order

    def fiat_market_sell(self, product_id: str, fiat_amount: str) -> Dict[str, Any]:
        """
        Place a market sell order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to sell (e.g., "BTC-USDC").
            fiat_amount (str): The amount of fiat currency to receive.

        Returns:
            dict: The order response from Coinbase.
        """
        spot_price = self.get_spot_price(product_id)
        base_increment = Decimal(self.get_product(product_id)['base_increment'])
        base_size = self._calculate_base_size(Decimal(fiat_amount), spot_price, base_increment)
        
        order = self.market_order_sell(self._generate_client_order_id(), product_id, str(base_size))
        self._log_order_result(order, product_id, fiat_amount, Side.SELL)
        return order

    def fiat_limit_buy(self, product_id: str, fiat_amount: str, price_multiplier: float = BUY_PRICE_MULTIPLIER) -> Dict[str, Any]:
        """
        Places a limit buy order.

        Args:
            product_id (str): The ID of the product to buy (e.g., "BTC-USD").
            fiat_amount (str): The amount in fiat currency to spend on buying.
            price_multiplier (float, optional): Multiplier to apply to the current spot price to get the limit price.
                                                Defaults to BUY_PRICE_MULTIPLIER.

        Returns:
            Dict[str, Any]: The response containing order details.
        """
        return self._place_limit_order(product_id, fiat_amount, price_multiplier, Side.BUY)

    def fiat_limit_sell(self, product_id: str, fiat_amount: str, price_multiplier: float = SELL_PRICE_MULTIPLIER) -> Dict[str, Any]:
        """
        Places a limit sell order.

        Args:
            product_id (str): The ID of the product to sell (e.g., "BTC-USD").
            fiat_amount (str): The amount in USD or other fiat to receive from selling (e.g., "200").
            price_multiplier (float, optional): Multiplier to apply to the current spot price to get the limit price.
                                                Defaults to SELL_PRICE_MULTIPLIER.

        Returns:
            Dict[str, Any]: The response of the order details.
        """
        return self._place_limit_order(product_id, fiat_amount, price_multiplier, Side.SELL)

    def _place_limit_order(self, product_id: str, fiat_amount: str, price_multiplier: float, side: Side) -> Dict[str, Any]:
        product_details = self.get_product(product_id)
        quote_increment = Decimal(product_details['quote_increment'])
        base_increment = Decimal(product_details['base_increment'])

        spot_price = self.get_spot_price(product_id)
        limit_price = (Decimal(spot_price) * Decimal(price_multiplier)).quantize(quote_increment)

        fiat_amount_decimal = Decimal(fiat_amount)
        effective_fiat_amount = fiat_amount_decimal * (1 - self.MAKER_FEE_RATE) if side == Side.BUY else fiat_amount_decimal / (1 - self.MAKER_FEE_RATE)
        base_size = (effective_fiat_amount / limit_price).quantize(base_increment, rounding=ROUND_HALF_UP)

        order_func = self.limit_order_gtc_buy if side == Side.BUY else self.limit_order_gtc_sell
        order = order_func(
            self._generate_client_order_id(),
            product_id,
            str(base_size),
            str(limit_price)
        )

        self._log_order_result(order, product_id, base_size, limit_price, side)

        return order

    def _log_order_result(self, order: Dict[str, Any], product_id: str, amount: Any, price: Any = None, side: Side = None) -> None:
        """
        Log the result of an order.

        Args:
            order (Dict[str, Any]): The order response from Coinbase.
            product_id (str): The ID of the product.
            amount (Any): The amount of the order.
            price (Any, optional): The price of the order (for limit orders).
            side (Side, optional): The side of the order (buy or sell).
        """
        base_currency, quote_currency = product_id.split('-')
        order_type = "limit" if price else "market"
        side_str = side.name.lower() if side else "unknown"

        if order['success']:
            if price:
                total_amount = Decimal(amount) * Decimal(price)
                logger.info(f"Successfully placed a {order_type} {side_str} order for {amount} {base_currency} "
                            f"(${total_amount:.2f}) at a price of {price} {quote_currency}.")
            else:
                logger.info(f"Successfully placed a {order_type} {side_str} order for {amount} {quote_currency} of {base_currency}.")
        else:
            failure_reason = order.get('failure_reason', 'Unknown')
            preview_failure_reason = order.get('error_response', {}).get('preview_failure_reason', 'Unknown')
            logger.error(f"Failed to place a {order_type} {side_str} order. Reason: {failure_reason}. Preview failure reason: {preview_failure_reason}")
        
        logger.debug(f"Coinbase response: {order}")