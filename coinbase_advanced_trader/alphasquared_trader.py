from decimal import Decimal, ROUND_DOWN
import logging
from .enhanced_rest_client import EnhancedRESTClient
from alphasquared import AlphaSquared
from coinbase_advanced_trader.models import Order

logger = logging.getLogger(__name__)

class AlphaSquaredTrader:
    def __init__(self, coinbase_client: EnhancedRESTClient, alphasquared_client: AlphaSquared):
        self.coinbase_client = coinbase_client
        self.alphasquared_client = alphasquared_client

    def execute_strategy(self, product_id: str, strategy_name: str):
        try:
            asset, base_currency = product_id.split('-')
            
            current_risk = self.alphasquared_client.get_current_risk(asset)
            logger.info(f"Current {asset} Risk: {current_risk}")
            
            action, value = self.alphasquared_client.get_strategy_value_for_risk(strategy_name, current_risk)
            logger.info(f"Strategy suggests: Action = {action.upper()}, Value = {value}")
            
            if value <= 0:
                logger.info("No action taken based on current risk and strategy.")
                return
            
            if action.lower() == 'buy':
                self._execute_buy(product_id, value)
            elif action.lower() == 'sell':
                self._execute_sell(product_id, asset, base_currency, value)
            else:
                logger.info(f"Unknown action: {action}. No trade executed.")
        
        except Exception as e:
            logger.error(f"Error in execute_strategy: {str(e)}")
            logger.exception("Full traceback:")

    def _execute_buy(self, product_id: str, value: float):
        try:
            order = self.coinbase_client.fiat_limit_buy(product_id, str(value), price_multiplier="0.995")
            if isinstance(order, Order):
                logger.info(f"Buy limit order placed: ID={order.id}, Size={order.size}, Price={order.price}")
            else:
                logger.warning(f"Unexpected order response type: {type(order)}")
        except Exception as e:
            logger.error(f"Error placing buy order: {str(e)}")
            logger.exception("Full traceback:")

    def _execute_sell(self, product_id, asset, base_currency, value):
        balance = Decimal(self.coinbase_client.get_crypto_balance(asset))
        logger.info(f"Current {asset} balance: {balance}")
        
        product_details = self.coinbase_client.get_product(product_id)
        base_increment = Decimal(product_details['base_increment'])
        quote_increment = Decimal(product_details['quote_increment'])
        current_price = Decimal(product_details['price'])
        logger.info(f"Current {asset} price: {current_price} {base_currency}")

        sell_amount = (balance * Decimal(value) / Decimal('100')).quantize(base_increment, rounding=ROUND_DOWN)
        logger.info(f"Sell amount: {sell_amount} {asset}")

        if sell_amount > base_increment:
            limit_price = (current_price * Decimal('1.005')).quantize(quote_increment, rounding=ROUND_DOWN)
            
            order = self.coinbase_client.limit_order_gtc_sell(
                client_order_id=self.coinbase_client._order_service._generate_client_order_id(),
                product_id=product_id,
                base_size=str(sell_amount),
                limit_price=str(limit_price)
            )
            
            logger.info(f"Sell limit order placed for {sell_amount} {asset} at {limit_price} {base_currency}: {order}")
        else:
            logger.info(f"Sell amount {sell_amount} {asset} is too small. Minimum allowed is {base_increment}. No order placed.")
