import json
import unittest
from decimal import Decimal
from unittest.mock import Mock, patch

from coinbase_advanced_trader.services.websocket_service import WebsocketService


def ticker_message():
    return json.dumps({
        "channel": "ticker",
        "client_id": "",
        "timestamp": "2026-05-03T12:00:00Z",
        "sequence_num": 1,
        "events": [{
            "type": "update",
            "tickers": [{
                "product_id": "BTC-USDC",
                "price": "65000.12",
                "best_bid": "65000.01",
                "best_ask": "65000.23"
            }]
        }]
    })


def ticker_message_without_envelope_defaults():
    return json.dumps({
        "channel": "ticker",
        "events": [{
            "type": "update",
            "tickers": [{
                "product_id": "BTC-USD",
                "price": "65000.12",
                "best_bid": "65000.01",
                "best_ask": "65000.23"
            }]
        }]
    })


def user_order_message(status="FILLED"):
    return json.dumps({
        "channel": "user",
        "client_id": "",
        "timestamp": "2026-05-03T12:00:00Z",
        "sequence_num": 2,
        "events": [{
            "type": "update",
            "orders": [{
                "order_id": "order-123",
                "product_id": "BTC-USDC",
                "status": status,
                "order_side": "BUY",
                "avg_price": "50000",
                "cumulative_quantity": "0.0002",
                "filled_value": "10",
                "total_fees": "0.05"
            }]
        }]
    })


class TestWebsocketService(unittest.TestCase):
    def setUp(self):
        self.rest_client = Mock()
        self.rest_client.api_key = "organizations/org/apiKeys/key"
        self.rest_client.api_secret = "secret"
        self.rest_client.is_authenticated = True
        self.service = WebsocketService(self.rest_client)

    @patch("coinbase_advanced_trader.services.websocket_service.WSClient")
    def test_watch_ticker_parses_prices(self, mock_ws_client_cls):
        ws_client = Mock()

        def make_client(**kwargs):
            ws_client.sleep_with_exception_check.side_effect = (
                lambda seconds: kwargs["on_message"](ticker_message())
            )
            return ws_client

        mock_ws_client_cls.side_effect = make_client

        updates = self.service.watch_ticker(
            ["BTC-USDC"],
            seconds=1,
            print_prices=False
        )

        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0].product_id, "BTC-USDC")
        self.assertEqual(updates[0].price, Decimal("65000.12"))
        ws_client.open.assert_called_once()
        ws_client.ticker.assert_called_once_with(["BTC-USDC"])
        ws_client.close.assert_called_once()

    @patch("coinbase_advanced_trader.services.websocket_service.WSClient")
    def test_watch_ticker_accepts_live_messages_without_envelope_defaults(
        self,
        mock_ws_client_cls
    ):
        ws_client = Mock()

        def make_client(**kwargs):
            ws_client.sleep_with_exception_check.side_effect = (
                lambda seconds: kwargs["on_message"](
                    ticker_message_without_envelope_defaults()
                )
            )
            return ws_client

        mock_ws_client_cls.side_effect = make_client

        updates = self.service.watch_ticker(
            ["BTC-USDC"],
            seconds=1,
            print_prices=False
        )

        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0].product_id, "BTC-USD")
        self.assertEqual(updates[0].price, Decimal("65000.12"))

    @patch("coinbase_advanced_trader.services.websocket_service.WSUserClient")
    def test_wait_for_order_fill_returns_matching_fill(self, mock_ws_user_client_cls):
        ws_client = Mock()

        def make_client(**kwargs):
            ws_client.sleep_with_exception_check.side_effect = (
                lambda seconds: kwargs["on_message"](user_order_message())
            )
            return ws_client

        mock_ws_user_client_cls.side_effect = make_client

        fill = self.service.wait_for_order_fill(
            "order-123",
            "BTC-USDC",
            timeout=1
        )

        self.assertTrue(fill.is_filled)
        self.assertEqual(fill.order_id, "order-123")
        self.assertEqual(fill.filled_size, Decimal("0.0002"))
        self.assertEqual(fill.average_filled_price, Decimal("50000"))
        self.assertEqual(fill.filled_value, Decimal("10"))
        ws_client.heartbeats.assert_called_once()
        ws_client.user.assert_called_once_with(["BTC-USDC"])
        ws_client.close.assert_called_once()

    @patch("coinbase_advanced_trader.services.websocket_service.WSUserClient")
    def test_wait_for_order_fill_raises_on_terminal_non_fill(self, mock_ws_user_client_cls):
        ws_client = Mock()

        def make_client(**kwargs):
            ws_client.sleep_with_exception_check.side_effect = (
                lambda seconds: kwargs["on_message"](user_order_message("CANCELLED"))
            )
            return ws_client

        mock_ws_user_client_cls.side_effect = make_client

        with self.assertRaises(RuntimeError):
            self.service.wait_for_order_fill(
                "order-123",
                "BTC-USDC",
                timeout=1
            )

    @patch("coinbase_advanced_trader.services.websocket_service.WSUserClient")
    def test_place_order_and_wait_for_fill_subscribes_before_order(self, mock_ws_user_client_cls):
        ws_client = Mock()
        call_order = []
        placed_order = Mock()
        placed_order.id = "order-123"

        def make_client(**kwargs):
            ws_client.user.side_effect = lambda product_ids: call_order.append("subscribed")
            ws_client.sleep_with_exception_check.side_effect = (
                lambda seconds: kwargs["on_message"](user_order_message())
            )
            return ws_client

        def place_order():
            call_order.append("placed")
            return placed_order

        mock_ws_user_client_cls.side_effect = make_client

        order, fill = self.service.place_order_and_wait_for_fill(
            "BTC-USDC",
            place_order=place_order,
            timeout=1
        )

        self.assertEqual(call_order, ["subscribed", "placed"])
        self.assertEqual(order, placed_order)
        self.assertTrue(fill.is_filled)
        ws_client.close.assert_called_once()

    def test_authenticated_helpers_require_keys(self):
        self.rest_client.is_authenticated = False

        with self.assertRaises(ValueError):
            self.service.watch_order_events("BTC-USDC", seconds=1)


if __name__ == "__main__":
    unittest.main()
