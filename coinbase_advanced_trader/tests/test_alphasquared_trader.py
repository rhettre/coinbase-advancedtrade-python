import unittest
from unittest.mock import Mock, patch
from decimal import Decimal
from coinbase_advanced_trader.alphasquared_trader import AlphaSquaredTrader
from coinbase_advanced_trader.models import Order, OrderSide, OrderType

class TestAlphaSquaredTrader(unittest.TestCase):
    def setUp(self):
        self.mock_coinbase_client = Mock()
        self.mock_alphasquared_client = Mock()
        self.trader = AlphaSquaredTrader(self.mock_coinbase_client, self.mock_alphasquared_client)

    def test_execute_strategy_buy(self):
        self.mock_alphasquared_client.get_current_risk.return_value = 30
        self.mock_alphasquared_client.get_strategy_value_for_risk.return_value = ('buy', 100)
        
        mock_order = Order(
            id='123',
            product_id='BTC-USDC',
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            size=Decimal('0.001'),
            price=Decimal('50000')
        )
        self.mock_coinbase_client.fiat_limit_buy.return_value = mock_order

        self.trader.execute_strategy('BTC-USDC', 'TestStrategy')

        self.mock_alphasquared_client.get_current_risk.assert_called_once_with('BTC')
        self.mock_alphasquared_client.get_strategy_value_for_risk.assert_called_once_with('TestStrategy', 30)
        self.mock_coinbase_client.fiat_limit_buy.assert_called_once_with('BTC-USDC', '100', price_multiplier='0.995')

    def test_execute_strategy_sell(self):
        self.mock_alphasquared_client.get_current_risk.return_value = 70
        self.mock_alphasquared_client.get_strategy_value_for_risk.return_value = ('sell', 50)
        
        self.mock_coinbase_client.get_crypto_balance.return_value = '1.0'
        self.mock_coinbase_client.get_product.return_value = {
            'base_increment': '0.00000001',
            'quote_increment': '0.01',
            'price': '50000'
        }
        
        mock_order = Order(
            id='456',
            product_id='BTC-USDC',
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            size=Decimal('0.5'),
            price=Decimal('50250')
        )
        self.mock_coinbase_client.limit_order_gtc_sell.return_value = mock_order

        self.trader.execute_strategy('BTC-USDC', 'TestStrategy')

        self.mock_alphasquared_client.get_current_risk.assert_called_once_with('BTC')
        self.mock_alphasquared_client.get_strategy_value_for_risk.assert_called_once_with('TestStrategy', 70)
        self.mock_coinbase_client.get_crypto_balance.assert_called_once_with('BTC')
        self.mock_coinbase_client.get_product.assert_called_once_with('BTC-USDC')
        self.mock_coinbase_client.limit_order_gtc_sell.assert_called_once()

if __name__ == '__main__':
    unittest.main()