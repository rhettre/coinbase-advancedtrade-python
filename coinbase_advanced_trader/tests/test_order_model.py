import unittest
from decimal import Decimal

from coinbase_advanced_trader.models.order import Order, OrderSide, OrderType


class TestOrderModel(unittest.TestCase):
    """Test cases for the Order model."""

    def test_order_creation(self):
        """Test the creation of an Order instance."""
        order = Order(
            id='fb67bb54-73ba-41ec-a038-9883664325b7',
            product_id='BTC-USDC',
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            size=Decimal('0.01'),
            price=Decimal('10000'),
            client_order_id='12345678901'
        )

        self.assertEqual(order.id, 'fb67bb54-73ba-41ec-a038-9883664325b7')
        self.assertEqual(order.product_id, 'BTC-USDC')
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.type, OrderType.LIMIT)
        self.assertEqual(order.size, Decimal('0.01'))
        self.assertEqual(order.price, Decimal('10000'))
        self.assertEqual(order.client_order_id, '12345678901')
        self.assertEqual(order.status, 'pending')

    def test_order_properties(self):
        """Test the properties of different Order types."""
        buy_market_order = Order(
            id='007e54c1-9e53-4afc-93f1-92cd5e98bc20',
            product_id='BTC-USDC',
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            size=Decimal('10')
        )

        self.assertTrue(buy_market_order.is_buy)
        self.assertFalse(buy_market_order.is_sell)
        self.assertTrue(buy_market_order.is_market)
        self.assertFalse(buy_market_order.is_limit)

        sell_limit_order = Order(
            id='fb67bb54-73ba-41ec-a038-9883664325b7',
            product_id='BTC-USDC',
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            size=Decimal('0.01'),
            price=Decimal('10000')
        )

        self.assertFalse(sell_limit_order.is_buy)
        self.assertTrue(sell_limit_order.is_sell)
        self.assertFalse(sell_limit_order.is_market)
        self.assertTrue(sell_limit_order.is_limit)

    def test_limit_order_without_price(self):
        """Test that creating a limit order without price raises ValueError."""
        with self.assertRaises(ValueError):
            Order(
                id='test-id',
                product_id='BTC-USDC',
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                size=Decimal('0.01')
            )


if __name__ == '__main__':
    unittest.main()