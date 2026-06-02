"""High-level WebSocket workflows for Coinbase Advanced Trade."""

import copy
import json
import time
from dataclasses import dataclass
from decimal import Decimal
from queue import Queue
from typing import Any, Callable, List, Optional, Sequence, Tuple, Union

from coinbase.websocket import WSClient, WSUserClient, WebsocketResponse

from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.utils import ensure_dict


TERMINAL_NON_FILL_STATUSES = {
    "CANCELLED",
    "EXPIRED",
    "FAILED",
    "REJECTED",
}


@dataclass
class TickerUpdate:
    """A simplified ticker update from the Coinbase WebSocket feed."""

    product_id: str
    price: Optional[Decimal]
    best_bid: Optional[Decimal]
    best_ask: Optional[Decimal]
    raw_ticker: Any


@dataclass
class OrderEvent:
    """A simplified user-channel order event."""

    order_id: str
    product_id: str
    status: str
    side: Optional[str]
    filled_size: Decimal
    average_filled_price: Decimal
    filled_value: Decimal
    total_fees: Decimal
    raw_order: Any

    @property
    def is_filled(self) -> bool:
        """Return True when Coinbase reports this order as filled."""
        return self.status == "FILLED"


class WebsocketService:
    """Beginner-friendly WebSocket workflows built on the official SDK."""

    def __init__(self, rest_client: Any):
        self.rest_client = rest_client

    def watch_ticker(
        self,
        product_ids: Union[str, Sequence[str]],
        seconds: int = 10,
        callback: Optional[Callable[[TickerUpdate], None]] = None,
        print_prices: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> List[TickerUpdate]:
        """
        Watch live ticker prices for a short demo-friendly window.

        Args:
            product_ids: Product IDs like "BTC-USDC" or ["BTC-USDC", "ETH-USDC"].
            seconds: How long to keep the connection open.
            callback: Optional function called once for every parsed ticker update.
            print_prices: Print a simple line for each ticker when no callback is used.
            retry: Whether the official SDK should reconnect on dropped connections.
            verbose: Enable official SDK WebSocket debug logging.

        Returns:
            A list of parsed ticker updates seen during the watch window.
        """
        if seconds <= 0:
            raise ValueError("seconds must be greater than 0")

        updates: List[TickerUpdate] = []
        product_ids_list = self._coerce_product_ids(product_ids)

        def on_message(message: str) -> None:
            response = self._parse_message(message)
            if not response or response.channel != "ticker":
                return

            for ticker_update in self._ticker_updates_from_response(response):
                updates.append(ticker_update)
                if callback:
                    callback(ticker_update)
                elif print_prices:
                    self._print_ticker_update(ticker_update)

        ws_client = WSClient(on_message=on_message, retry=retry, verbose=verbose)
        ws_client.open()
        try:
            ws_client.ticker(product_ids_list)
            ws_client.sleep_with_exception_check(seconds)
        finally:
            self._close_ws_client(ws_client)

        return updates

    def watch_prices(
        self,
        product_ids: Union[str, Sequence[str]],
        seconds: int = 10,
        callback: Optional[Callable[[TickerUpdate], None]] = None,
        print_prices: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> List[TickerUpdate]:
        """Alias for watch_ticker that reads naturally in beginner tutorials."""
        return self.watch_ticker(
            product_ids=product_ids,
            seconds=seconds,
            callback=callback,
            print_prices=print_prices,
            retry=retry,
            verbose=verbose,
        )

    def watch_order_events(
        self,
        product_ids: Union[str, Sequence[str]],
        callback: Optional[Callable[[OrderEvent], None]] = None,
        seconds: Optional[int] = None,
        include_heartbeats: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> List[OrderEvent]:
        """
        Watch authenticated user-channel order events.

        Pass seconds for tutorial/demo runs. Leave it as None for a long-running bot.
        """
        self._require_authentication()
        events: List[OrderEvent] = []
        product_ids_list = self._coerce_product_ids(product_ids)

        def on_message(message: str) -> None:
            response = self._parse_message(message)
            if not response or response.channel != "user":
                return

            for order_event in self._order_events_from_response(response):
                events.append(order_event)
                if callback:
                    callback(order_event)

        ws_client = self._build_user_ws_client(
            on_message=on_message,
            retry=retry,
            verbose=verbose,
        )
        ws_client.open()
        try:
            if include_heartbeats:
                ws_client.heartbeats()
            ws_client.user(product_ids_list)

            if seconds is None:
                ws_client.run_forever_with_exception_check()
            else:
                ws_client.sleep_with_exception_check(seconds)
        except KeyboardInterrupt:
            logger.info("Stopped watching order events.")
        finally:
            self._close_ws_client(ws_client)

        return events

    def wait_for_order_fill(
        self,
        order_id: str,
        product_id: Union[str, Sequence[str]],
        timeout: int = 300,
        callback: Optional[Callable[[OrderEvent], None]] = None,
        include_heartbeats: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> OrderEvent:
        """
        Block until Coinbase reports that a specific order is filled.

        Raises TimeoutError if the fill is not seen before timeout. Raises
        RuntimeError if Coinbase sends a terminal non-fill status first.
        """
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")

        self._require_authentication()
        product_ids_list = self._coerce_product_ids(product_id)
        events: Queue[OrderEvent] = Queue()

        def on_message(message: str) -> None:
            response = self._parse_message(message)
            if not response or response.channel != "user":
                return

            for order_event in self._order_events_from_response(response):
                events.put(order_event)

        ws_client = self._build_user_ws_client(
            on_message=on_message,
            retry=retry,
            verbose=verbose,
        )
        ws_client.open()
        try:
            if include_heartbeats:
                ws_client.heartbeats()
            ws_client.user(product_ids_list)

            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                remaining = max(0.0, deadline - time.monotonic())
                ws_client.sleep_with_exception_check(min(1.0, remaining))

                fill = self._pop_fill_event(events, order_id, callback)
                if fill:
                    return fill
        finally:
            self._close_ws_client(ws_client)

        raise TimeoutError(f"Timed out waiting for order {order_id} to fill.")

    def place_order_and_wait_for_fill(
        self,
        product_id: Union[str, Sequence[str]],
        place_order: Callable[[], Any],
        timeout: int = 300,
        callback: Optional[Callable[[OrderEvent], None]] = None,
        include_heartbeats: bool = True,
        retry: bool = True,
        verbose: bool = False,
    ) -> Tuple[Any, OrderEvent]:
        """
        Open the user WebSocket, place an order, then wait for its fill event.

        This avoids missing fast fills from market orders because the user stream
        is already subscribed before the REST order request is sent.
        """
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")

        self._require_authentication()
        product_ids_list = self._coerce_product_ids(product_id)
        events: Queue[OrderEvent] = Queue()

        def on_message(message: str) -> None:
            response = self._parse_message(message)
            if not response or response.channel != "user":
                return

            for order_event in self._order_events_from_response(response):
                events.put(order_event)

        ws_client = self._build_user_ws_client(
            on_message=on_message,
            retry=retry,
            verbose=verbose,
        )
        ws_client.open()
        try:
            if include_heartbeats:
                ws_client.heartbeats()
            ws_client.user(product_ids_list)

            order = place_order()
            order_id = getattr(order, "id", None)
            if not order_id:
                raise ValueError("Placed order did not return an id.")

            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                fill = self._pop_fill_event(events, order_id, callback)
                if fill:
                    return order, fill

                remaining = max(0.0, deadline - time.monotonic())
                ws_client.sleep_with_exception_check(min(1.0, remaining))
        finally:
            self._close_ws_client(ws_client)

        raise TimeoutError(f"Timed out waiting for order {order_id} to fill.")

    def _build_user_ws_client(
        self,
        on_message: Callable[[str], None],
        retry: bool,
        verbose: bool,
    ) -> WSUserClient:
        return WSUserClient(
            api_key=self.rest_client.api_key,
            api_secret=self.rest_client.api_secret,
            on_message=on_message,
            retry=retry,
            verbose=verbose,
        )

    def _require_authentication(self) -> None:
        if not getattr(self.rest_client, "is_authenticated", False):
            raise ValueError(
                "Authenticated WebSocket helpers require api_key and api_secret."
            )

    def _coerce_product_ids(self, product_ids: Union[str, Sequence[str]]) -> List[str]:
        if isinstance(product_ids, str):
            return [product_ids]

        product_ids_list = list(product_ids)
        if not product_ids_list:
            raise ValueError("At least one product_id is required")

        return product_ids_list

    def _parse_message(self, message: Union[str, dict]) -> Optional[WebsocketResponse]:
        try:
            data = json.loads(message) if isinstance(message, str) else message
            if "channel" not in data or "events" not in data:
                return None
            data.setdefault("client_id", "")
            data.setdefault("timestamp", "")
            data.setdefault("sequence_num", 0)
            return WebsocketResponse(copy.deepcopy(data))
        except Exception as error:
            logger.debug(f"Skipping unparseable WebSocket message: {error}")
            return None

    def _ticker_updates_from_response(
        self,
        response: WebsocketResponse
    ) -> List[TickerUpdate]:
        updates: List[TickerUpdate] = []
        for event in response.events:
            for ticker in getattr(event, "tickers", None) or []:
                updates.append(
                    TickerUpdate(
                        product_id=getattr(ticker, "product_id", ""),
                        price=self._to_decimal(getattr(ticker, "price", None)),
                        best_bid=self._to_decimal(getattr(ticker, "best_bid", None)),
                        best_ask=self._to_decimal(getattr(ticker, "best_ask", None)),
                        raw_ticker=ticker,
                    )
                )
        return updates

    def _order_events_from_response(
        self,
        response: WebsocketResponse
    ) -> List[OrderEvent]:
        order_events: List[OrderEvent] = []
        for event in response.events:
            for user_order in getattr(event, "orders", None) or []:
                filled_size = self._to_decimal(
                    getattr(user_order, "cumulative_quantity", None)
                )
                filled_value = self._to_decimal(getattr(user_order, "filled_value", None))
                average_filled_price = self._to_decimal(getattr(user_order, "avg_price", None))

                if average_filled_price == Decimal("0") and filled_size > 0:
                    average_filled_price = filled_value / filled_size

                order_events.append(
                    OrderEvent(
                        order_id=getattr(user_order, "order_id", ""),
                        product_id=getattr(user_order, "product_id", ""),
                        status=(getattr(user_order, "status", "") or "").upper(),
                        side=getattr(user_order, "order_side", None),
                        filled_size=filled_size,
                        average_filled_price=average_filled_price,
                        filled_value=filled_value,
                        total_fees=self._to_decimal(getattr(user_order, "total_fees", None)),
                        raw_order=ensure_dict(user_order),
                    )
                )
        return order_events

    def _pop_fill_event(
        self,
        events: Queue[OrderEvent],
        order_id: str,
        callback: Optional[Callable[[OrderEvent], None]] = None,
    ) -> Optional[OrderEvent]:
        while not events.empty():
            order_event = events.get()
            if order_event.order_id != order_id:
                continue

            if callback:
                callback(order_event)

            if order_event.is_filled:
                return order_event

            if order_event.status in TERMINAL_NON_FILL_STATUSES:
                raise RuntimeError(
                    f"Order {order_id} reached {order_event.status} before filling."
                )

        return None

    def _to_decimal(self, value: Any) -> Decimal:
        if value in (None, ""):
            return Decimal("0")

        return Decimal(str(value))

    def _print_ticker_update(self, ticker_update: TickerUpdate) -> None:
        price = ticker_update.price if ticker_update.price is not None else "unknown"
        print(f"{ticker_update.product_id}: {price}")

    def _close_ws_client(self, ws_client: Any) -> None:
        try:
            ws_client.close()
        except Exception as error:
            logger.debug(f"WebSocket close skipped or failed: {error}")
