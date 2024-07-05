from coinbase_advanced_trader.config import config_manager
from coinbase_advanced_trader.logger import logger

BUY_PRICE_MULTIPLIER = config_manager.get('BUY_PRICE_MULTIPLIER')
SELL_PRICE_MULTIPLIER = config_manager.get('SELL_PRICE_MULTIPLIER')
FEAR_AND_GREED_API_URL = config_manager.get('FEAR_AND_GREED_API_URL')

class TradingConfig:
    def __init__(self):
        self._fgi_schedule = [
            {'threshold': 10, 'factor': 1.5, 'action': 'buy'},
            {'threshold': 20, 'factor': 1.3, 'action': 'buy'},
            {'threshold': 30, 'factor': 1.1, 'action': 'buy'},
            {'threshold': 40, 'factor': 1.0, 'action': 'buy'},
            {'threshold': 50, 'factor': 0.9, 'action': 'buy'},
            {'threshold': 60, 'factor': 0.7, 'action': 'buy'},
            {'threshold': 70, 'factor': 1, 'action': 'sell'},
            {'threshold': 80, 'factor': 1.5, 'action': 'sell'},
            {'threshold': 90, 'factor': 2, 'action': 'sell'}
        ]

    def update_fgi_schedule(self, new_schedule):
        if self.validate_schedule(new_schedule):
            self._fgi_schedule = new_schedule
            logger.info("FGI schedule updated.")
        else:
            logger.error("Invalid FGI schedule. Update rejected.")
            raise ValueError("Invalid FGI schedule")

    def get_fgi_schedule(self):
        return self._fgi_schedule

    def validate_schedule(self, schedule):
        """
        Validate the given FGI schedule without updating it.

        Args:
            schedule (List[Dict]): The schedule to validate.

        Returns:
            bool: True if the schedule is valid, False otherwise.
        """
        if not schedule:
            logger.warning("Empty schedule provided.")
            return False
        
        last_buy_threshold = float('-inf')
        last_sell_threshold = float('inf')
        
        for condition in sorted(schedule, key=lambda x: x['threshold']):
            if 'threshold' not in condition or 'factor' not in condition or 'action' not in condition:
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
    