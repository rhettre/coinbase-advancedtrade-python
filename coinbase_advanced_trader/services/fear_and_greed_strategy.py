import time
from decimal import Decimal
from typing import Optional, Tuple

from fear_and_greed import FearAndGreedIndex

from coinbase_advanced_trader.config import config_manager
from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.models import Order
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
        self._fgi_client = FearAndGreedIndex()

    def execute_trade(self, product_id: str, fiat_amount: str) -> Optional[Order]:
        """
        Execute a trade based on the Fear and Greed Index (FGI).

        :param product_id: The product identifier for the trade.
        :param fiat_amount: The amount of fiat currency to trade.
        :return: An Order object if a trade is executed, None otherwise.
        """
        fgi = self._fgi_client.get_current_value()
        fgi_classification = self._fgi_client.get_current_classification()
        
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