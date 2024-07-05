import yaml
from pathlib import Path
from coinbase_advanced_trader.constants import DEFAULT_CONFIG

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.config_path = Path('config.yaml')
        self.config = self._load_config()

    def _load_config(self):
        config = DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                if user_config:
                    config.update(user_config)
            except Exception as e:
                print(f"Error loading user config: {e}")
        return config

    def get(self, key, default=None):
        return self.config.get(key, default)
    
    @classmethod
    def reset(cls):
        cls._instance = None

config_manager = ConfigManager()