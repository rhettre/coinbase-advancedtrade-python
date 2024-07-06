import unittest
from unittest.mock import patch
from coinbase_advanced_trader.legacy.strategies.fear_and_greed_strategies import get_fear_and_greed_index, trade_based_on_fgi_simple, trade_based_on_fgi_pro


class TestFearAndGreedStrategies(unittest.TestCase):

    @patch('coinbase_advanced_trader.legacy.strategies.fear_and_greed_strategies.requests.get')
    def test_get_fear_and_greed_index(self, mock_get):
        mock_get.return_value.json.return_value = {
            'data': [{'value': 50, 'value_classification': 'Neutral'}]}
        self.assertEqual(get_fear_and_greed_index(), (50, 'Neutral'))

    @patch('coinbase_advanced_trader.legacy.strategies.fear_and_greed_strategies.get_fear_and_greed_index')
    @patch('coinbase_advanced_trader.legacy.strategies.fear_and_greed_strategies.fiat_limit_buy')
    def test_trade_based_on_fgi_simple(self, mock_buy, mock_index):
        mock_index.return_value = (50, 'Neutral')
        mock_buy.return_value = {'status': 'success'}
        self.assertEqual(trade_based_on_fgi_simple(
            'BTC-USD', 100), {'status': 'success'})

    @patch('coinbase_advanced_trader.legacy.strategies.fear_and_greed_strategies.get_fear_and_greed_index')
    @patch('coinbase_advanced_trader.legacy.strategies.fear_and_greed_strategies.fiat_limit_buy')
    @patch('coinbase_advanced_trader.legacy.strategies.fear_and_greed_strategies.fiat_limit_sell')
    def test_trade_based_on_fgi_pro(self, mock_sell, mock_buy, mock_index):
        mock_index.return_value = (80, 'Greed')
        mock_sell.return_value = {'status': 'success'}
        self.assertEqual(trade_based_on_fgi_pro(
            'BTC-USD', 100), {'status': 'success'})


if __name__ == '__main__':
    unittest.main()
