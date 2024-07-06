"""Configuration management for Coinbase Advanced Trader."""

import logging
from pathlib import Path

import yaml

from coinbase_advanced_trader.constants import DEFAULT_CONFIG


class ConfigManager:
    """Singleton class for managing application configuration."""

    _instance = None

    def __new__(cls):
        """Create a new instance if one doesn't exist, otherwise return the existing instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        """Initialize the ConfigManager with default configuration and user overrides."""
        self.config_path = Path('config.yaml')
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from file, falling back to defaults if necessary."""
        config = DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                if user_config:
                    config.update(user_config)
            except Exception as e:
                logging.error(f"Error loading user config: {e}")
        return config

    def get(self, key, default=None):
        """Retrieve a configuration value by key, with an optional default."""
        return self.config.get(key, default)

    @classmethod
    def reset(cls):
        """Reset the singleton instance."""
        cls._instance = None


config_manager = ConfigManager()