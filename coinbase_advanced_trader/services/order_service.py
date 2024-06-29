from typing import Dict, Any
from decimal import Decimal
import uuid
from coinbase.rest import RESTClient
from coinbase_advanced_trader.models import Order, OrderSide, OrderType
from coinbase_advanced_trader.config import BUY_PRICE_MULTIPLIER, SELL_PRICE_MULTIPLIER
from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.utils import calculate_base_size
from .price_service import PriceService

class OrderService:
    def __init__(self, rest_client: RESTClient, price_service: PriceService):
        self.rest_client = rest_client
        self.MAKER_FEE_RATE = Decimal('0.006')
        self.price_service = price_service

    def _generate_client_order_id(self) -> str:
        return str(uuid.uuid4())

    def fiat_market_buy(self, product_id: str, fiat_amount: str) -> Order:
        order_response = self.rest_client.market_order_buy(self._generate_client_order_id(), product_id, fiat_amount)
        order = Order(
            id=order_response['order_id'],
            product_id=product_id,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            size=Decimal(fiat_amount)
        )
        # Pass the required arguments to _log_order_result
        self._log_order_result(order_response, product_id, fiat_amount)
        return order

    def fiat_market_sell(self, product_id: str, fiat_amount: str) -> Order:
        """
        Place a market sell order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to sell (e.g., "BTC-USDC").
            fiat_amount (str): The amount of fiat currency to receive.

        Returns:
            Order: The order object containing details about the executed order.
        """
        spot_price = self.price_service.get_spot_price(product_id)
        product_details = self.price_service.get_product_details(product_id)
        base_increment = Decimal(product_details['base_increment'])
        base_size = calculate_base_size(Decimal(fiat_amount), spot_price, base_increment)

        order_response = self.rest_client.market_order_sell(self._generate_client_order_id(), product_id, str(base_size))
        order = Order(
            id=order_response['order_id'],
            product_id=product_id,
            side=OrderSide.SELL,
            type=OrderType.MARKET,
            size=base_size
        )
        self._log_order_result(order_response, product_id, str(base_size), spot_price, OrderSide.SELL)
        return order

    def fiat_limit_buy(self, product_id: str, fiat_amount: str, price_multiplier: float = BUY_PRICE_MULTIPLIER) -> Order:
        return self._place_limit_order(product_id, fiat_amount, price_multiplier, OrderSide.BUY)

    def fiat_limit_sell(self, product_id: str, fiat_amount: str, price_multiplier: float = SELL_PRICE_MULTIPLIER) -> Order:
        return self._place_limit_order(product_id, fiat_amount, price_multiplier, OrderSide.SELL)

    def _place_limit_order(self, product_id: str, fiat_amount: str, price_multiplier: float, side: OrderSide) -> Order:
        current_price = self.price_service.get_spot_price(product_id)
        adjusted_price = current_price * Decimal(price_multiplier)
        product_details = self.price_service.get_product_details(product_id)
        base_increment = Decimal(product_details['base_increment'])
        base_size = calculate_base_size(Decimal(fiat_amount), adjusted_price, base_increment)
        
        order_func = self.rest_client.limit_order_buy if side == OrderSide.BUY else self.rest_client.limit_order_sell
        order_response = order_func(self._generate_client_order_id(), product_id, str(base_size), str(adjusted_price))
        
        order = Order(
            id=order_response['order_id'],
            product_id=product_id,
            side=side,
            type=OrderType.LIMIT,
            size=base_size,
            price=adjusted_price
        )
        self._log_order_result(order)
        return order
    
    def _place_limit_order(self, product_id: str, fiat_amount: str, price_multiplier: float, side: OrderSide) -> Order:
        current_price = self.price_service.get_spot_price(product_id)
        adjusted_price = current_price * Decimal(price_multiplier)
        product_details = self.price_service.get_product_details(product_id)
        base_increment = Decimal(product_details['base_increment'])
        quote_increment = Decimal(product_details['quote_increment'])

        # Quantize the adjusted price and base size according to the product details
        adjusted_price = adjusted_price.quantize(quote_increment)
        base_size = calculate_base_size(Decimal(fiat_amount), adjusted_price, base_increment)
        base_size = base_size.quantize(base_increment)

        order_func = self.rest_client.limit_order_gtc_buy if side == OrderSide.BUY else self.rest_client.limit_order_gtc_sell
        order_response = order_func(self._generate_client_order_id(), product_id, str(base_size), str(adjusted_price))
        
        order = Order(
            id=order_response['order_id'],
            product_id=product_id,
            side=side,
            type=OrderType.LIMIT,
            size=base_size,
            price=adjusted_price
        )
        self._log_order_result(order_response, product_id, base_size, adjusted_price, side)
        return order
    
    def _log_order_result(self, order: Dict[str, Any], product_id: str, amount: Any, price: Any = None, side: OrderSide = None) -> None:
        """
        Log the result of an order.

        Args:
        order (Dict[str, Any]): The order response from Coinbase.
        product_id (str): The ID of the product.
        amount (Any): The actual amount of the order.
        price (Any, optional): The price of the order (for limit orders).
        side (OrderSide, optional): The side of the order (buy or sell).
        """
        base_currency, quote_currency = product_id.split('-')
        order_type = "limit" if price else "market"
        side_str = side.name.lower() if side else "unknown"

        if order['success']:
            if price:
                total_amount = Decimal(amount) * Decimal(price)
                log_message = (f"Successfully placed a {order_type} {side_str} order for {amount} {base_currency} "
                               f"(${total_amount:.2f}) at a price of {price} {quote_currency}.")
            else:
                log_message = f"Successfully placed a {order_type} {side_str} order for {amount} {quote_currency} of {base_currency}."

            logger.info(log_message)
        else:
            failure_reason = order.get('failure_reason', 'Unknown')
            preview_failure_reason = order.get('error_response', {}).get('preview_failure_reason', 'Unknown')
            logger.error(f"Failed to place a {order_type} {side_str} order. Reason: {failure_reason}. Preview failure reason: {preview_failure_reason}")
        
        logger.debug(f"Coinbase response: {order}")