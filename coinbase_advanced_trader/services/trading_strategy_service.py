import requests
from typing import List, Dict, Any
from decimal import Decimal
from coinbase_advanced_trader.models import Order
from coinbase_advanced_trader.config import FGI_SCHEDULE, FEAR_AND_GREED_API_URL
from coinbase_advanced_trader.logger import logger
from .order_service import OrderService
from .price_service import PriceService

class TradingStrategyService:
    def __init__(self, order_service: OrderService, price_service: PriceService):
        self.order_service = order_service
        self.price_service = price_service

    def get_fear_and_greed_index(self) -> tuple:
        response = requests.get(FEAR_AND_GREED_API_URL)
        data = response.json()['data'][0]
        return int(data['value']), data['value_classification']

    def _execute_trade(self, product_id: str, fiat_amount: str, action: str) -> Order:
        if action == 'buy':
            return self.order_service.fiat_limit_buy(product_id, fiat_amount)
        elif action == 'sell':
            return self.order_service.fiat_limit_sell(product_id, fiat_amount)
        else:
            logger.error(f"Invalid action: {action}")
            return None

    def trade_based_on_fgi(self, product_id: str, fiat_amount: str, schedule: List[Dict[str, Any]] = None) -> Order:
        if schedule is None:
            schedule = FGI_SCHEDULE  # Ensure a default schedule is used if none is provided

        fgi, fgi_classification = self.get_fear_and_greed_index()
        logger.info(f"FGI retrieved: {fgi} ({fgi_classification}) for trading {product_id}")
        
        fiat_amount = Decimal(fiat_amount)  # Convert fiat_amount to Decimal before multiplication
        
        for condition in schedule:
            if ((condition['action'] == 'buy' and fgi <= condition['threshold']) or
                (condition['action'] == 'sell' and fgi >= condition['threshold'])):
                adjusted_amount = fiat_amount * Decimal(condition['factor'])
                logger.info(f"FGI condition met: FGI {fgi} {condition['action']} condition. Executing {condition['action']} with adjusted amount {adjusted_amount:.2f}")
                return self._execute_trade(product_id, str(adjusted_amount), condition['action'])

        logger.warning(f"No trading condition met for FGI: {fgi}")
        return None