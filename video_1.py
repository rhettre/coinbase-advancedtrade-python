"""
Video 1 demo script:
Coinbase Advanced Trade WebSocket API Tutorial | Official Python SDK

This file is intentionally gitignored. It is a local filming/demo aid, not
package source code.

The teaching arc for this video:
1. REST asks Coinbase questions. WebSocket lets Coinbase push live events.
2. Public ticker data works without an API key.
3. WebsocketResponse turns raw JSON into Python objects.
4. Heartbeats are a useful quiet-channel keepalive / health signal.
5. Trader use cases decide the transport: slow REST bars, live WebSocket fills.
6. The authenticated user channel can report order updates live.
7. Optional: place one tiny real order and watch the fill event arrive.

Run:
    python video_1.py

Environment for authenticated section:
    export COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
    export COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\\n...\\n-----END EC PRIVATE KEY-----\\n"
"""

import copy
import json
import os
import shlex
import time
import uuid
from decimal import Decimal
from pathlib import Path
from queue import Queue
from typing import Any, Optional

from coinbase.rest import RESTClient
from coinbase.websocket import WSClient, WSUserClient, WebsocketResponse


ENV_VIDEO_FILE = Path(__file__).with_name(".env.video")

# Public ticker products. These are safe because public ticker streams do not
# require credentials and do not place orders.
PUBLIC_PRODUCTS = ["BTC-USDC"]
PUBLIC_SECONDS = 10

# Authenticated user-channel demo products. Keep this focused on the product
# you might place a tiny order for on camera.
USER_PRODUCTS = ["BTC-USDC"]
USER_CHANNEL_SECONDS = 45

# This spends real money when the trigger condition is met.
PLACE_REAL_MARKET_BUY = True
REAL_BUY_PRODUCT_ID = "BTC-USDC"
REAL_BUY_QUOTE_SIZE = "10"
BUY_TRIGGER_PRODUCT_ID = "BTC-USDC"
BUY_TRIGGER_PRICE = Decimal("80920")
BUY_TRIGGER_ABOVE_READS_REQUIRED = 3


def load_env_video(path: Path = ENV_VIDEO_FILE) -> bool:
    """
    Load KEY=value pairs from .env.video for local filming.

    Existing shell environment variables win. The loader intentionally avoids
    printing secret values and supports the quoted KEY=value format used in
    VIDEO_1_SCRIPT.md and VIDEO_DEMO_RUNBOOK.md.
    """
    if not path.exists():
        return False

    def parse_env_value(value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            return ""
        if stripped_value[0] in {"'", '"'}:
            try:
                parsed_value = shlex.split(stripped_value, comments=True, posix=True)
            except ValueError:
                return stripped_value.strip("'\"")
            return parsed_value[0] if parsed_value else ""
        return stripped_value

    loaded_any = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        key, separator, value = line.partition("=")
        if not separator:
            continue

        key = key.strip()
        if not key or os.getenv(key):
            continue

        os.environ[key] = parse_env_value(value)
        loaded_any = True

    return loaded_any


def parse_ws_message(raw_message: str) -> Optional[WebsocketResponse]:
    """
    Convert the raw JSON string from Coinbase into WebsocketResponse.

    - The official SDK callback gives us raw JSON text.
    - json.loads turns that text into a dict.
    - WebsocketResponse turns the dict into typed-ish Python objects like
      response.channel, response.events, event.tickers, and event.orders.
    - copy.deepcopy matters because WebsocketResponse pops keys while parsing.
    """
    try:
        message_dict = json.loads(raw_message)
    except json.JSONDecodeError:
        print("Received a non-JSON message:", raw_message)
        return None

    if "channel" not in message_dict:
        # Subscription acknowledgements or misc messages may not look like a
        # market/user event. For a beginner video, it is clearer to skip them.
        return None

    if "events" not in message_dict:
        # Coinbase may send channel metadata/subscription messages that are not
        # market data or user events. They are useful internally, but not useful
        # for this beginner demo.
        return None

    # The official parser expects these envelope fields. Live messages from the
    # feed can omit client_id, especially when no client ID was supplied, so we
    # add harmless defaults for tutorial parsing.
    message_dict.setdefault("client_id", "")
    message_dict.setdefault("timestamp", "")
    message_dict.setdefault("sequence_num", 0)

    try:
        return WebsocketResponse(copy.deepcopy(message_dict))
    except Exception as error:
        # Keep the filming demo running if Coinbase sends a message type the
        # parser does not model yet. Raw JSON is still available while debugging.
        print(f"Skipping unsupported WebSocket message: {error}")
        return None


def response_to_dict(response: Any) -> Any:
    """
    Tiny demo helper for official SDK response objects.

    The REST SDK returns response objects, not always plain dicts. The objects
    usually support to_dict(), which is convenient for demos and logging.
    """
    if response is None:
        return {}
    if isinstance(response, dict):
        return {key: response_to_dict(value) for key, value in response.items()}
    if isinstance(response, list):
        return [response_to_dict(item) for item in response]
    if hasattr(response, "to_dict"):
        return response_to_dict(response.to_dict())
    if hasattr(response, "__dict__"):
        return {
            key: response_to_dict(value)
            for key, value in vars(response).items()
            if not key.startswith("_")
        }
    return response


def demo_public_ticker_stream() -> None:
    print("\n=== Public ticker stream: no API key required ===")

    def on_message(raw_message: str) -> None:
        response = parse_ws_message(raw_message)
        if not response:
            return

        if response.channel == "ticker":
            for event in response.events:
                for ticker in event.tickers or []:
                    print(
                        f"{ticker.product_id:8} "
                        f"price={ticker.price:>12} "
                        f"bid={ticker.best_bid:>12} "
                        f"ask={ticker.best_ask:>12}"
                    )

        if response.channel == "heartbeats":
            for event in response.events:
                print(f"heartbeat #{event.heartbeat_counter} at {event.current_time}")

    ws_client = WSClient(on_message=on_message)
    ws_client.open()
    try:
        ws_client.ticker(PUBLIC_PRODUCTS)
        ws_client.heartbeats()
        ws_client.sleep_with_exception_check(PUBLIC_SECONDS)
    finally:
        ws_client.close()


def demo_parse_one_message_without_a_websocket() -> None:
    """
    Segment 2: explain WebsocketResponse without waiting on live data.

    This segment is useful if you want a calm cutaway after the live ticker
    starts scrolling. It shows the exact shape of the object you get after
    parsing a WebSocket message.
    """
    print("\n=== WebsocketResponse parsing walkthrough ===")

    fake_raw_message = json.dumps({
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
                "best_ask": "65000.23",
            }],
        }],
    })

    response = parse_ws_message(fake_raw_message)
    ticker = response.events[0].tickers[0]

    print("response.channel:", response.channel)
    print("response.timestamp:", response.timestamp)
    print("ticker.product_id:", ticker.product_id)
    print("ticker.price:", Decimal(ticker.price))


def demo_trader_transport_map() -> None:
    """
    Segment 2.5: connect the WebSocket lesson to real trader workflows.
    """
    print("\n=== Trader workflow map: REST vs WebSocket ===")
    print("Vol-targeted trend: REST daily candles build the signal.")
    print("Take-profit automation: REST places orders; WebSocket confirms fills.")
    print("24/7 bot: WebSocket logs account events; REST recovers reference state.")
    print("Market making: level2/trades/user streams are advanced, not Video 1.")


def demo_authenticated_user_channel() -> None:
    """
    Safe default:
    - The script subscribes to the user channel if API keys exist.
    - It does not place an order unless PLACE_REAL_MARKET_BUY is True.

    Filming option:
    - Start this segment with PLACE_REAL_MARKET_BUY=False and place/cancel an
      order manually in Coinbase to show that the script sees account events.
    - Or flip PLACE_REAL_MARKET_BUY=True for the on-camera tiny order moment.
    """
    loaded_env_video = load_env_video()
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")

    if not api_key or not api_secret:
        print("\n=== Authenticated user channel skipped ===")
        print(
            "Set COINBASE_API_KEY and COINBASE_API_SECRET in your shell or "
            "in .env.video to run this segment."
        )
        return

    if loaded_env_video:
        print(f"\nLoaded authenticated demo credentials from {ENV_VIDEO_FILE.name}.")

    print("\n=== Authenticated user channel: live account/order events ===")
    order_events = Queue()
    rest_client = RESTClient(api_key=api_key, api_secret=api_secret)
    above_trigger_price_reads = 0
    waiting_for_drop = False
    buy_order_placed = False

    def place_triggered_market_buy(trigger_price: Decimal) -> None:
        nonlocal buy_order_placed

        if not PLACE_REAL_MARKET_BUY:
            return

        buy_order_placed = True
        print(
            "\nTrigger met: saw "
            f"{BUY_TRIGGER_ABOVE_READS_REQUIRED} BTC-USDC prices above "
            f"{BUY_TRIGGER_PRICE}, then {trigger_price} below {BUY_TRIGGER_PRICE}."
        )
        print(
            f"Placing a real ${REAL_BUY_QUOTE_SIZE} market buy on "
            f"{REAL_BUY_PRODUCT_ID}. This spends real money."
        )
        order_response = rest_client.market_order_buy(
            client_order_id=uuid.uuid4().hex,
            product_id=REAL_BUY_PRODUCT_ID,
            quote_size=REAL_BUY_QUOTE_SIZE,
        )
        print("REST order response:")
        print(json.dumps(response_to_dict(order_response), indent=2))

    def watch_price_trigger(raw_message: str) -> None:
        nonlocal above_trigger_price_reads, waiting_for_drop

        if buy_order_placed:
            return

        response = parse_ws_message(raw_message)
        if not response or response.channel != "ticker":
            return

        for event in response.events:
            for ticker in event.tickers or []:
                if ticker.product_id not in {BUY_TRIGGER_PRODUCT_ID, "BTC-USD"}:
                    continue

                price = Decimal(ticker.price)
                print(
                    f"trigger watch {ticker.product_id:8} "
                    f"price={price} "
                    f"above_reads={above_trigger_price_reads}/"
                    f"{BUY_TRIGGER_ABOVE_READS_REQUIRED}"
                )

                if not waiting_for_drop:
                    if price > BUY_TRIGGER_PRICE:
                        above_trigger_price_reads += 1
                        if above_trigger_price_reads >= BUY_TRIGGER_ABOVE_READS_REQUIRED:
                            waiting_for_drop = True
                            print(
                                f"Armed buy trigger. Next BTC-USDC price below "
                                f"{BUY_TRIGGER_PRICE} places the real buy."
                            )
                    else:
                        above_trigger_price_reads = 0
                    return

                if price < BUY_TRIGGER_PRICE:
                    place_triggered_market_buy(price)
                    return

    def on_message(raw_message: str) -> None:
        response = parse_ws_message(raw_message)
        if not response:
            return

        if response.channel == "heartbeats":
            # Keep this quieter than the ticker section. Heartbeats prove the
            # connection is alive even when no order updates are happening.
            return

        if response.channel != "user":
            return

        for event in response.events:
            for order in event.orders or []:
                order_events.put(order)
                print(
                    f"user event order_id={order.order_id} "
                    f"product={order.product_id} "
                    f"status={order.status} "
                    f"side={order.order_side} "
                    f"filled={order.cumulative_quantity} "
                    f"avg_price={order.avg_price}"
                )

    user_ws = WSUserClient(
        api_key=api_key,
        api_secret=api_secret,
        on_message=on_message,
    )
    price_ws = WSClient(on_message=watch_price_trigger)

    user_ws.open()
    price_ws.open()
    try:
        user_ws.heartbeats()
        user_ws.user(USER_PRODUCTS)
        price_ws.ticker([BUY_TRIGGER_PRODUCT_ID])
        price_ws.heartbeats()

        if PLACE_REAL_MARKET_BUY:
            print("\nReal-money trigger is enabled.")
            print(
                f"Waiting for {BUY_TRIGGER_ABOVE_READS_REQUIRED} BTC-USDC prices "
                f"above {BUY_TRIGGER_PRICE}, then one below {BUY_TRIGGER_PRICE}."
            )
        else:
            print(
                "\nNot placing an order because PLACE_REAL_MARKET_BUY=False. "
                "You can place/cancel an order manually now, or flip the flag."
            )

        deadline = time.monotonic() + USER_CHANNEL_SECONDS
        while time.monotonic() < deadline:
            user_ws.sleep_with_exception_check(1)
            price_ws.sleep_with_exception_check(0)

        print(f"\nCaptured {order_events.qsize()} user-channel order event(s).")
    finally:
        price_ws.close()
        user_ws.close()


def main() -> None:
    print(__doc__)
    #demo_public_ticker_stream()
    demo_parse_one_message_without_a_websocket()
    demo_authenticated_user_channel()


if __name__ == "__main__":
    main()
