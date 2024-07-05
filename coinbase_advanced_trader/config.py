import yaml
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_path = Path('config.yaml')
        self.config = self._load_config()

    def _load_config(self):
        default_config = {
            'BUY_PRICE_MULTIPLIER': 0.9995,
            'SELL_PRICE_MULTIPLIER': 1.005,
            'FEAR_AND_GREED_API_URL': 'https://api.alternative.me/fng/?limit=1',
            'LOG_FILE_PATH': 'coinbase_advanced_trader.log',
            'LOG_LEVEL': 'DEBUG',
            'FGI_CACHE_DURATION': 3600
        }

        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                user_config = yaml.safe_load(f)
            default_config.update(user_config)

        return default_config

    def get(self, key, default=None):
        return self.config.get(key, default)

config_manager = ConfigManager()