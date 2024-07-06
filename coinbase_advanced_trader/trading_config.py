"""Trading configuration module for Coinbase Advanced Trader."""

from typing import List, Dict, Any
from coinbase_advanced_trader.config import config_manager
from coinbase_advanced_trader.logger import logger

BUY_PRICE_MULTIPLIER = config_manager.get('BUY_PRICE_MULTIPLIER')
SELL_PRICE_MULTIPLIER = config_manager.get('SELL_PRICE_MULTIPLIER')
FEAR_AND_GREED_API_URL = config_manager.get('FEAR_AND_GREED_API_URL')


class FearAndGreedConfig:
    """Manages trading configuration and Fear and Greed Index (FGI) schedule."""

    def __init__(self) -> None:
        """Initialize TradingConfig with default FGI schedule."""
        self._fgi_schedule: List[Dict[str, Any]] = [
            {'threshold': 10, 'factor': 1.5, 'action': 'buy'},
            {'threshold': 20, 'factor': 1.3, 'action': 'buy'},
            {'threshold': 30, 'factor': 1.1, 'action': 'buy'},
            {'threshold': 40, 'factor': 1.0, 'action': 'buy'},
            {'threshold': 50, 'factor': 0.9, 'action': 'buy'},
            {'threshold': 60, 'factor': 0.7, 'action': 'buy'},
            {'threshold': 70, 'factor': 1.0, 'action': 'sell'},
            {'threshold': 80, 'factor': 1.5, 'action': 'sell'},
            {'threshold': 90, 'factor': 2.0, 'action': 'sell'}
        ]

    def update_fgi_schedule(self, new_schedule: List[Dict[str, Any]]) -> None:
        """
        Update the FGI schedule if valid.

        Args:
            new_schedule: The new schedule to be set.

        Raises:
            ValueError: If the provided schedule is invalid.
        """
        if self.validate_schedule(new_schedule):
            self._fgi_schedule = new_schedule
            logger.info("FGI schedule updated.")
        else:
            logger.error("Invalid FGI schedule. Update rejected.")
            raise ValueError("Invalid FGI schedule")

    def get_fgi_schedule(self) -> List[Dict[str, Any]]:
        """
        Get the current FGI schedule.

        Returns:
            The current FGI schedule.
        """
        return self._fgi_schedule

    def validate_schedule(self, schedule: List[Dict[str, Any]]) -> bool:
        """
        Validate the given FGI schedule without updating it.

        Args:
            schedule: The schedule to validate.

        Returns:
            True if the schedule is valid, False otherwise.
        """
        if not schedule:
            logger.warning("Empty schedule provided.")
            return False

        last_buy_threshold = float('-inf')
        last_sell_threshold = float('inf')

        for condition in sorted(schedule, key=lambda x: x['threshold']):
            if not all(key in condition for key in ('threshold', 'factor', 'action')):
                logger.warning(f"Invalid condition format: {condition}")
                return False

            if condition['action'] == 'buy':
                if condition['threshold'] >= last_sell_threshold:
                    logger.warning(f"Invalid buy threshold: {condition['threshold']}")
                    return False
                last_buy_threshold = condition['threshold']
            elif condition['action'] == 'sell':
                if condition['threshold'] <= last_buy_threshold:
                    logger.warning(f"Invalid sell threshold: {condition['threshold']}")
                    return False
                last_sell_threshold = condition['threshold']
            else:
                logger.warning(f"Invalid action: {condition['action']}")
                return False

        logger.info("FGI schedule is valid.")
        return True
