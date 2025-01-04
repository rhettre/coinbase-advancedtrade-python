import uuid
from decimal import Decimal
from typing import Dict, Any, Optional

from coinbase.rest import RESTClient

from coinbase_advanced_trader.models import Order, OrderSide, OrderType
from coinbase_advanced_trader.trading_config import (
    BUY_PRICE_MULTIPLIER,
    SELL_PRICE_MULTIPLIER
)
from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.utils import calculate_base_size
from .price_service import PriceService


class OrderService:
    """Service for handling order-related operations."""

    def __init__(self, rest_client: RESTClient, price_service: PriceService):
        """
        Initialize the OrderService.

        Args:
            rest_client (RESTClient): The REST client for API calls.
            price_service (PriceService): The service for price-related operations.
        """
        self.rest_client = rest_client
        self.price_service = price_service
        self.MAKER_FEE_RATE = Decimal('0.006')

    def _generate_client_order_id(self) -> str:
        """Generate a unique client order ID."""
        return str(uuid.uuid4())

    def fiat_market_buy(self, product_id: str, fiat_amount: str) -> Order:
        """
        Place a market buy order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to buy.
            fiat_amount (str): The amount of fiat currency to spend.

        Returns:
            Order: The order object containing details about the executed order.

        Raises:
            Exception: If the order placement fails.
        """
        try:
            order_response = self.rest_client.market_order_buy(
                self._generate_client_order_id(), product_id, fiat_amount
            )
            if not order_response['success']:
                error_response = order_response.get('error_response', {})
                error_message = error_response.get('message', 'Unknown error')
                preview_failure_reason = error_response.get('preview_failure_reason', 'Unknown')
                error_log = (f"Failed to place a market buy order. "
                             f"Reason: {error_message}. "
                             f"Preview failure reason: {preview_failure_reason}")
                logger.error(error_log)
                raise Exception(error_log)
            
            order = Order(
                id=order_response['success_response']['order_id'],
                product_id=product_id,
                side=OrderSide.BUY,
                type=OrderType.MARKET,
                size=Decimal(fiat_amount)
            )
            self._log_order_result(order_response, product_id, fiat_amount, side=OrderSide.BUY)
            return order
        except Exception as e:
            error_message = str(e)
            if "Invalid product_id" in error_message:
                error_log = (f"Failed to place a market buy order. "
                             f"Reason: {error_message}. "
                             f"Preview failure reason: Unknown")
                logger.error(error_log)
            raise

    def fiat_market_sell(self, product_id: str, fiat_amount: str) -> Order:
        """
        Place a market sell order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to sell (e.g., "BTC-USDC").
            fiat_amount (str): The amount of fiat currency to receive.

        Returns:
            Order: The order object containing details about the executed order.

        Raises:
            Exception: If the order placement fails.
        """
        spot_price = self.price_service.get_spot_price(product_id)
        product_details = self.price_service.get_product_details(product_id)
        base_increment = Decimal(product_details['base_increment'])
        base_size = calculate_base_size(Decimal(fiat_amount), spot_price, base_increment)
        
        try:
            order_response = self.rest_client.market_order_sell(
                self._generate_client_order_id(), product_id, str(base_size)
            )
            if not order_response['success']:
                error_response = order_response.get('error_response', {})
                error_message = error_response.get('message', 'Unknown error')
                preview_failure_reason = error_response.get('preview_failure_reason', 'Unknown')
                error_log = (f"Failed to place a market sell order. "
                             f"Reason: {error_message}. "
                             f"Preview failure reason: {preview_failure_reason}")
                logger.error(error_log)
                raise Exception(error_log)
            
            order = Order(
                id=order_response['success_response']['order_id'],
                product_id=product_id,
                side=OrderSide.SELL,
                type=OrderType.MARKET,
                size=base_size
            )
            self._log_order_result(order_response, product_id, str(base_size), side=OrderSide.SELL)
            return order
        except Exception as e:
            error_message = str(e)
            if "Invalid product_id" in error_message:
                error_log = (f"Failed to place a market sell order. "
                             f"Reason: {error_message}. "
                             f"Preview failure reason: Unknown")
                logger.error(error_log)
            raise

    def fiat_limit_buy(self, product_id: str, fiat_amount: str, limit_price: Optional[str] = None, price_multiplier: float = BUY_PRICE_MULTIPLIER) -> Order:
        """
        Place a limit buy order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to buy.
            fiat_amount (str): The amount of fiat currency to spend.
            limit_price (Optional[str]): The specific limit price for the order (overrides price_multiplier if provided).
            price_multiplier (float): The multiplier for the current price (used if limit_price is not provided).

        Returns:
            Order: The order object containing details about the executed order.
        """
        return self._place_limit_order(product_id, fiat_amount, limit_price, price_multiplier, OrderSide.BUY)

    def fiat_limit_sell(self, product_id: str, fiat_amount: str, limit_price: Optional[str] = None, price_multiplier: float = SELL_PRICE_MULTIPLIER) -> Order:
        """
        Place a limit sell order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to sell.
            fiat_amount (str): The amount of fiat currency to receive.
            limit_price (Optional[str]): The specific limit price for the order (overrides price_multiplier if provided).
            price_multiplier (float): The multiplier for the current price (used if limit_price is not provided).

        Returns:
            Order: The order object containing details about the executed order.
        """
        return self._place_limit_order(product_id, fiat_amount, limit_price, price_multiplier, OrderSide.SELL)
    
    def _place_limit_order(self, product_id: str, fiat_amount: str, limit_price: Optional[str], price_multiplier: float, side: OrderSide) -> Order:
        """
        Place a limit order.

        Args:
            product_id (str): The ID of the product.
            fiat_amount (str): The amount of fiat currency.
            limit_price (Optional[str]): The specific limit price for the order.
            price_multiplier (float): The multiplier for the current price.
            side (OrderSide): The side of the order (buy or sell).

        Returns:
            Order: The order object containing details about the executed order.
        """
        logger.info(f"Starting limit order placement - Side: {side}, Product: {product_id}")
        
        current_price = self.price_service.get_spot_price(product_id)
        if current_price is None:
            raise ValueError(f"Could not get current price for {product_id}")
        
        product_details = self.price_service.get_product_details(product_id)
        if product_details is None:
            raise ValueError(f"Could not get product details for {product_id}")

        base_increment = Decimal(product_details['base_increment'])
        quote_increment = Decimal(product_details['quote_increment'])

        # Calculate adjusted price
        adjusted_price = (Decimal(limit_price) if limit_price 
                        else current_price * Decimal(str(price_multiplier))).quantize(quote_increment)

        # Calculate base size
        base_size = calculate_base_size(Decimal(fiat_amount), adjusted_price, base_increment)

        # Place the order
        order_func = (self.rest_client.limit_order_gtc_buy 
                    if side == OrderSide.BUY 
                    else self.rest_client.limit_order_gtc_sell)
        
        order_response = order_func(
            self._generate_client_order_id(),
            product_id,
            str(base_size),
            str(adjusted_price)
        )
        
        order = Order(
            id=order_response['success_response']['order_id'],
            product_id=product_id,
            side=side,
            type=OrderType.LIMIT,
            size=base_size,
            price=adjusted_price
        )
        
        # Pass fiat_amount for buy orders, base_size for sell orders
        amount = fiat_amount if side == OrderSide.BUY else str(base_size)
        self._log_order_result(order_response, product_id, amount, adjusted_price, side)
        return order
    
    def _log_order_result(self, order: Dict[str, Any], product_id: str, amount: Any, price: Any = None, side: OrderSide = None) -> None:
        """
        Log the result of an order.

        Args:
            order (Dict[str, Any]): The order response from Coinbase.
            product_id (str): The ID of the product.
            amount (Any): The actual amount of the order.
            price (Any, optional): The limit price for limit orders, or spot price for market orders.
            side (OrderSide, optional): The side of the order (buy or sell).
        """
        base_currency, quote_currency = product_id.split('-')
        side_str = side.name.lower() if side else "unknown"

        # Get product details for proper rounding
        product_details = self.price_service.get_product_details(product_id)
        if not product_details:
            raise ValueError(f"Could not get product details for {product_id}")
        
        base_increment = Decimal(product_details['base_increment'])
        quote_increment = Decimal(product_details['quote_increment'])

        if order['success']:
            spot_price = price if price else self.price_service.get_spot_price(product_id)
            
            if side == OrderSide.BUY:
                if price:  # Limit order
                    base_amount = (Decimal(amount) / Decimal(price)).quantize(base_increment)
                    log_message = (f"Successfully placed a limit buy order "
                                 f"for {Decimal(amount).quantize(quote_increment)} {quote_currency} of {base_currency} "
                                 f"(~{base_amount} {base_currency}) at {Decimal(price).quantize(quote_increment)} {quote_currency}")
                else:  # Market order
                    base_amount = (Decimal(amount) / Decimal(spot_price)).quantize(base_increment)
                    log_message = (f"Successfully placed a market buy order "
                                 f"for {Decimal(amount).quantize(quote_increment)} {quote_currency} of {base_currency} "
                                 f"(~{base_amount} {base_currency}) at {Decimal(spot_price).quantize(quote_increment)} {quote_currency}")
            else:  # SELL
                if price:  # Limit order
                    fiat_amount = (Decimal(amount) * Decimal(price)).quantize(quote_increment)
                    log_message = (f"Successfully placed a limit sell order "
                                 f"for {fiat_amount} {quote_currency} of {base_currency} "
                                 f"(~{Decimal(amount).quantize(base_increment)} {base_currency}) at {Decimal(price).quantize(quote_increment)} {quote_currency}")
                else:  # Market order
                    fiat_amount = (Decimal(amount) * Decimal(spot_price)).quantize(quote_increment)
                    log_message = (f"Successfully placed a market sell order "
                                 f"for {fiat_amount} {quote_currency} of {base_currency} "
                                 f"(~{Decimal(amount).quantize(base_increment)} {base_currency}) at {Decimal(spot_price).quantize(quote_increment)} {quote_currency}")
            logger.info(log_message)
        else:
            failure_reason = order.get('failure_reason', 'Unknown')
            preview_failure_reason = order.get('error_response', {}).get('preview_failure_reason', 'Unknown')
            order_type = "limit" if price else "market"
            logger.error(f"Failed to place a {order_type} {side_str} order. "
                        f"Reason: {failure_reason}. "
                        f"Preview failure reason: {preview_failure_reason}")
        
        logger.debug(f"Coinbase response: {order}")