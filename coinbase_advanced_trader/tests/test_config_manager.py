import unittest
from unittest.mock import patch, mock_open
from coinbase_advanced_trader.config import ConfigManager
from coinbase_advanced_trader.constants import DEFAULT_CONFIG


class TestConfigManager(unittest.TestCase):
    """Test cases for the ConfigManager class."""

    def setUp(self):
        """Set up the test environment before each test method."""
        self.default_config = DEFAULT_CONFIG
        ConfigManager.reset()

    @patch('coinbase_advanced_trader.config.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_config_with_existing_file(self, mock_yaml_load, mock_file,
                                            mock_exists):
        """Test loading config from an existing file."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            'BUY_PRICE_MULTIPLIER': 0.9990,
            'SELL_PRICE_MULTIPLIER': 1.010,
            'LOG_LEVEL': 'INFO'
        }

        config_manager = ConfigManager()
        test_config = config_manager.config
        
        self.assertEqual(test_config['BUY_PRICE_MULTIPLIER'], 0.9990)
        self.assertEqual(test_config['SELL_PRICE_MULTIPLIER'], 1.010)
        self.assertEqual(test_config['LOG_LEVEL'], 'INFO')

    @patch('coinbase_advanced_trader.config.Path.exists')
    def test_load_config_without_existing_file(self, mock_exists):
        """Test loading config when the file doesn't exist."""
        mock_exists.return_value = False

        config_manager = ConfigManager()
        test_config = config_manager.config

        self.assertEqual(test_config, self.default_config)


if __name__ == '__main__':
    unittest.main()