import time
from decimal import Decimal
from typing import Optional, Tuple

import requests

from coinbase_advanced_trader.config import config_manager
from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.models import Order
from coinbase_advanced_trader.trading_config import FEAR_AND_GREED_API_URL
from .trading_strategy_service import BaseTradingStrategy


class FearAndGreedStrategy(BaseTradingStrategy):
    """
    A trading strategy based on the Fear and Greed Index (FGI).
    """

    def __init__(self, order_service, price_service, config):
        """
        Initialize the FearAndGreedStrategy.

        :param order_service: Service for handling orders.
        :param price_service: Service for handling prices.
        :param config: Configuration object.
        """
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
        logger.info(f"FGI retrieved: {fgi} ({fgi_classification}) "
                    f"for trading {product_id}")

        fiat_amount = Decimal(fiat_amount)
        schedule = self.config.get_fgi_schedule()

        for condition in schedule:
            if self._should_execute_trade(condition, fgi):
                adjusted_amount = fiat_amount * Decimal(condition['factor'])
                logger.info(f"FGI condition met: FGI {fgi} "
                            f"{condition['action']} condition. "
                            f"Executing {condition['action']} with "
                            f"adjusted amount {adjusted_amount:.2f}")
                return self._execute_trade(product_id, str(adjusted_amount),
                                           condition['action'])

        logger.warning(f"No trading condition met for FGI: {fgi}")
        return None

    def get_fear_and_greed_index(self) -> Tuple[int, str]:
        """
        Retrieve the Fear and Greed Index (FGI) from the API or cache.

        :return: A tuple containing the FGI value and classification.
        """
        current_time = time.time()
        cache_duration = config_manager.get('FGI_CACHE_DURATION')
        if (not self._fgi_cache or
                (current_time - self._last_fgi_fetch_time > cache_duration)):
            response = requests.get(FEAR_AND_GREED_API_URL)
            data = response.json()['data'][0]
            self._fgi_cache = (int(data['value']), data['value_classification'])
            self._last_fgi_fetch_time = current_time
        return self._fgi_cache

    def _execute_trade(self, product_id: str, fiat_amount: str,
                       action: str) -> Optional[Order]:
        """
        Execute a buy or sell trade based on the given action.

        :param product_id: The product identifier for the trade.
        :param fiat_amount: The amount of fiat currency to trade.
        :param action: The trade action ('buy' or 'sell').
        :return: An Order object if the trade is executed successfully,
                 None otherwise.
        """
        if action == 'buy':
            return self.order_service.fiat_limit_buy(product_id, fiat_amount)
        elif action == 'sell':
            return self.order_service.fiat_limit_sell(product_id, fiat_amount)
        else:
            logger.error(f"Invalid action: {action}")
            return None

    @staticmethod
    def _should_execute_trade(condition: dict, fgi: int) -> bool:
        """
        Determine if a trade should be executed based on the condition and FGI.

        :param condition: The trading condition.
        :param fgi: The current Fear and Greed Index value.
        :return: True if the trade should be executed, False otherwise.
        """
        return ((condition['action'] == 'buy' and fgi <= condition['threshold'])
                or (condition['action'] == 'sell' and
                    fgi >= condition['threshold']))