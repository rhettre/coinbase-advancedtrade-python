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

    def test_execute_pending_strategy_actions_buy_uses_default_portfolio_and_acknowledges(self):
        self.mock_alphasquared_client.get_strategy_actions.return_value = {
            'actions': [
                {'notificationId': 'act-1', 'type': 'BUY', 'amount': '25'}
            ]
        }
        self.mock_coinbase_client.get_portfolios.return_value = {
            'portfolios': [{'uuid': 'default-portfolio', 'type': 'DEFAULT'}]
        }
        order = Order(
            id='buy-order-id',
            product_id='BTC-USDC',
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            size=Decimal('0.0005'),
            price=Decimal('50000'),
            client_order_id='client-id'
        )
        self.mock_coinbase_client.fiat_limit_buy.return_value = order
        self.mock_alphasquared_client.update_strategy_action_status.return_value = {
            'status': 'success'
        }

        results = self.trader.execute_pending_strategy_actions(
            'BTC-USDC',
            strategy_name='My Strategy'
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, 'executed')
        self.assertEqual(results[0].portfolio_uuid, 'default-portfolio')
        self.mock_coinbase_client.get_portfolios.assert_called_once_with('DEFAULT')
        self.mock_coinbase_client.fiat_limit_buy.assert_called_once()
        _, kwargs = self.mock_coinbase_client.fiat_limit_buy.call_args
        self.assertEqual(kwargs['retail_portfolio_id'], 'default-portfolio')
        self.assertIsNotNone(kwargs['client_order_id'])
        self.mock_alphasquared_client.update_strategy_action_status.assert_called_once_with(
            notification_id='act-1',
            executed=True,
            strategy_name='My Strategy',
            strategy_id=None,
            timeout=None
        )

    def test_execute_pending_strategy_actions_sell_uses_explicit_portfolio_balance(self):
        self.mock_alphasquared_client.get_strategy_actions.return_value = {
            'actions': [
                {'notificationId': 'act-2', 'type': 'SELL', 'value': '50'}
            ]
        }
        self.mock_coinbase_client.get_crypto_balance.return_value = Decimal('2')
        self.mock_coinbase_client.get_product.return_value = {
            'base_increment': '0.00000001',
            'quote_increment': '0.01',
            'price': '50000'
        }
        order = Order(
            id='sell-order-id',
            product_id='BTC-USDC',
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            size=Decimal('1.00000000'),
            price=Decimal('50250.00'),
            client_order_id='client-id'
        )
        self.mock_coinbase_client.limit_sell_base_size.return_value = order
        self.mock_alphasquared_client.update_strategy_action_status.return_value = {
            'status': 'success'
        }

        results = self.trader.execute_pending_strategy_actions(
            'BTC-USDC',
            strategy_name='My Strategy',
            portfolio_uuid='portfolio-1'
        )

        self.assertEqual(results[0].status, 'executed')
        self.mock_coinbase_client.get_portfolios.assert_not_called()
        self.mock_coinbase_client.get_crypto_balance.assert_called_once_with(
            'BTC',
            retail_portfolio_id='portfolio-1'
        )
        self.mock_coinbase_client.limit_sell_base_size.assert_called_once_with(
            product_id='BTC-USDC',
            base_size='1.00000000',
            limit_price='50250.00',
            post_only=False,
            client_order_id=self.mock_coinbase_client.limit_sell_base_size.call_args.kwargs['client_order_id'],
            retail_portfolio_id='portfolio-1'
        )
        self.mock_alphasquared_client.update_strategy_action_status.assert_called_once()

    def test_execute_pending_strategy_actions_coinbase_failure_does_not_acknowledge(self):
        self.mock_alphasquared_client.get_strategy_actions.return_value = {
            'actions': [
                {'notificationId': 'act-3', 'type': 'BUY', 'amount': '25'}
            ]
        }
        self.mock_coinbase_client.get_portfolios.return_value = {
            'portfolios': [{'uuid': 'default-portfolio'}]
        }
        self.mock_coinbase_client.fiat_limit_buy.side_effect = Exception('coinbase failed')

        results = self.trader.execute_pending_strategy_actions(
            'BTC-USDC',
            strategy_name='My Strategy'
        )

        self.assertEqual(results[0].status, 'failed')
        self.assertIn('coinbase failed', results[0].reason)
        self.mock_alphasquared_client.update_strategy_action_status.assert_not_called()

    def test_execute_pending_strategy_actions_malformed_and_unknown_actions_are_skipped(self):
        self.mock_alphasquared_client.get_strategy_actions.return_value = {
            'actions': [
                {'notificationId': 'act-4', 'type': 'HOLD', 'amount': '10'},
                {'type': 'BUY', 'amount': '10'}
            ]
        }

        results = self.trader.execute_pending_strategy_actions(
            'BTC-USDC',
            strategy_name='My Strategy'
        )

        self.assertEqual([result.status for result in results], ['skipped', 'skipped'])
        self.mock_coinbase_client.fiat_limit_buy.assert_not_called()
        self.mock_coinbase_client.limit_sell_base_size.assert_not_called()
        self.mock_alphasquared_client.update_strategy_action_status.assert_not_called()

    def test_execute_pending_strategy_actions_missing_default_portfolio_raises(self):
        self.mock_alphasquared_client.get_strategy_actions.return_value = {
            'actions': [
                {'notificationId': 'act-5', 'type': 'BUY', 'amount': '25'}
            ]
        }
        self.mock_coinbase_client.get_portfolios.return_value = {'portfolios': []}

        with self.assertRaisesRegex(ValueError, 'default portfolio'):
            self.trader.execute_pending_strategy_actions(
                'BTC-USDC',
                strategy_name='My Strategy'
            )

        self.mock_coinbase_client.fiat_limit_buy.assert_not_called()
        self.mock_alphasquared_client.update_strategy_action_status.assert_not_called()

if __name__ == '__main__':
    unittest.main()
