import unittest
from coinbase_advanced_trader.trading_config import FearAndGreedConfig


class TestTradingConfig(unittest.TestCase):
    """Test cases for the TradingConfig class."""

    def setUp(self):
        """Set up the test environment before each test method."""
        self.config = FearAndGreedConfig()

    def test_fgi_schedule_initial_state(self):
        """Test the initial state of the Fear and Greed Index schedule."""
        initial_schedule = self.config.get_fgi_schedule()
        self.assertEqual(len(initial_schedule), 9)

    def test_update_fgi_schedule_valid(self):
        """Test updating the FGI schedule with valid data."""
        new_schedule = [{'threshold': 10, 'factor': 1.5, 'action': 'buy'}]
        self.assertTrue(self.config.validate_schedule(new_schedule))
        self.config.update_fgi_schedule(new_schedule)
        self.assertEqual(self.config.get_fgi_schedule(), new_schedule)

    def test_update_fgi_schedule_invalid(self):
        """Test updating the FGI schedule with invalid data."""
        invalid_schedule = [
            {'threshold': 10, 'factor': 1.5, 'action': 'invalid_action'}
        ]
        with self.assertRaises(ValueError):
            self.config.update_fgi_schedule(invalid_schedule)


if __name__ == '__main__':
    unittest.main()