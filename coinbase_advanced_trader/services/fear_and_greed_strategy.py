import time
import requests
from decimal import Decimal
from typing import Optional, Tuple
from .trading_strategy_service import BaseTradingStrategy
from coinbase_advanced_trader.config import config_manager
from coinbase_advanced_trader.trading_config import FEAR_AND_GREED_API_URL
from coinbase_advanced_trader.models import Order
from coinbase_advanced_trader.logger import logger

class FearAndGreedStrategy(BaseTradingStrategy):
    def __init__(self, order_service, price_service, config):
        super().__init__(order_service, price_service)
        self.config = config
        self._last_fgi_fetch_time: float = 0
        self._fgi_cache: Optional[Tuple[int, str]] = None

    def execute_trade(self, product_id: str, fiat_amount: str) -> Optional[Order]:
        """
        Execute a trade based on the Fear and Greed Index (FGI).

        :param product_id: The product identifier for the trade.
        :param fiat_amount: The amount of fiat currency to trade.
        :return: An Order object if a trade is executed, None otherwise.
        """
        fgi, fgi_classification = self.get_fear_and_greed_index()
        logger.info(f"FGI retrieved: {fgi} ({fgi_classification}) for trading {product_id}")
        
        fiat_amount = Decimal(fiat_amount)
        schedule = self.config.get_fgi_schedule()

        for condition in schedule:
            if ((condition['action'] == 'buy' and fgi <= condition['threshold']) or
                (condition['action'] == 'sell' and fgi >= condition['threshold'])):
                adjusted_amount = fiat_amount * Decimal(condition['factor'])
                logger.info(f"FGI condition met: FGI {fgi} {condition['action']} condition. "
                            f"Executing {condition['action']} with adjusted amount {adjusted_amount:.2f}")
                return self._execute_trade(product_id, str(adjusted_amount), condition['action'])

        logger.warning(f"No trading condition met for FGI: {fgi}")
        return None

    def get_fear_and_greed_index(self) -> Tuple[int, str]:
        """
        Retrieve the Fear and Greed Index (FGI) from the API or cache.

        :return: A tuple containing the FGI value and classification.
        """
        current_time = time.time()
        if not self._fgi_cache or (current_time - self._last_fgi_fetch_time > config_manager.get('FGI_CACHE_DURATION')):
            response = requests.get(FEAR_AND_GREED_API_URL)
            data = response.json()['data'][0]
            self._fgi_cache = (int(data['value']), data['value_classification'])
            self._last_fgi_fetch_time = current_time
        return self._fgi_cache

    def _execute_trade(self, product_id: str, fiat_amount: str, action: str) -> Optional[Order]:
        """
        Execute a buy or sell trade based on the given action.

        :param product_id: The product identifier for the trade.
        :param fiat_amount: The amount of fiat currency to trade.
        :param action: The trade action ('buy' or 'sell').
        :return: An Order object if the trade is executed successfully, None otherwise.
        """
        if action == 'buy':
            return self.order_service.fiat_limit_buy(product_id, fiat_amount)
        elif action == 'sell':
            return self.order_service.fiat_limit_sell(product_id, fiat_amount)
        else:
            logger.error(f"Invalid action: {action}")
            return None