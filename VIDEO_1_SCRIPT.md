# Video 1 Script Runbook: Official Coinbase SDK WebSocket Tutorial

Working title:

```text
Coinbase Advanced Trade WebSocket API Tutorial | Official Python SDK
```

Primary file:

```text
/Users/rhettre/Github/coinbase/coinbase-advancedtrade-python/video_1.py
```

This video is about the official Coinbase Advanced Trade Python SDK, not Rhett's wrapper package. The wrapper is only teased at the end as the next step.

## Core Promise

The viewer should leave understanding one durable mental model:

```text
REST asks Coinbase for the latest state.
WebSocket lets Coinbase push live events into your script.
```

The video should not be framed as:

- a complete WebSocket channel tour
- a profitable trading strategy
- a market-making tutorial
- a deployment tutorial
- a bot that is ready to run unattended

This is a foundational transport lesson: how to connect, subscribe, parse messages, use heartbeats, and watch order events.

## Technical Accuracy Brief

Use these notes to keep the scriptwriter honest.

### REST vs WebSocket

REST is request/response:

```text
My script sends a request -> Coinbase sends one response.
```

Example: asking Coinbase for the current product state or placing an order.

WebSocket is event-driven:

```text
My script opens a connection -> Coinbase pushes messages whenever subscribed events happen.
```

Example: ticker updates, heartbeat messages, and authenticated order updates.

Do not say REST is bad or obsolete. REST is still the right tool for many tasks: placing orders, fetching account snapshots, fetching daily candles, and recovering state after a WebSocket interruption.

### Coinbase WebSocket Endpoints

Coinbase documents two production WebSocket endpoints for Advanced Trade:

- Market data endpoint: public market data and most public channels.
- User order data endpoint: private order updates for the authenticated user.

The official SDK hides most of the endpoint plumbing:

- `WSClient` is the general market-data WebSocket client.
- `WSUserClient` is the authenticated user-order WebSocket client.

### Public vs Private Channels

Public channels do not require an API key. These include market-data channels like ticker, ticker batch, candles, level2, market trades, status, and heartbeats.

Private channels require authentication. The important private channel for this video is:

```text
user
```

The `user` channel sends order updates that include the authenticated user. It is the channel that makes the live fill demo possible.

### Heartbeats

Coinbase documents that most channels can close within 60-90 seconds if no updates are sent. Subscribing to the `heartbeats` channel helps keep subscriptions open and gives a visible "connection is still alive" signal.

Safe narration:

```text
Heartbeats are not price data. They are a regular signal from Coinbase that helps keep the connection alive and lets us know the stream has not gone quiet because the script died.
```

Avoid saying:

```text
Heartbeats guarantee my bot can never disconnect.
```

Production systems still need reconnect, resubscribe, and REST reconciliation logic.

### Product ID Nuance: BTC-USDC vs BTC-USD

The script uses:

```python
PUBLIC_PRODUCTS = ["BTC-USDC", "ETH-USDC"]
USER_PRODUCTS = ["BTC-USDC"]
```

Coinbase documents an important nuance:

- Most public channels map `-USDC` subscriptions to corresponding `-USD` market data.
- `-USDC` product IDs are specifically available on the `user` channel.
- `USDT-USDC` and `EURC-USDC` are exceptions available on all channels.

So it is expected if the public ticker prints:

```text
BTC-USD
ETH-USD
```

even though the script subscribes with:

```text
BTC-USDC
ETH-USDC
```

Safe narration:

```text
Notice Coinbase returns BTC-USD here. That is a product-ID nuance in the public feeds. For the authenticated user channel, I keep BTC-USDC because that is the product I may place the order on.
```

### WebsocketResponse

The SDK callback receives raw JSON text. The script turns that into a `WebsocketResponse` so the demo can use Python object fields like:

```python
response.channel
response.events
ticker.product_id
ticker.price
order.status
order.avg_price
```

Technical detail: the SDK's `WebsocketResponse` parser expects envelope fields such as `client_id`, `timestamp`, `sequence_num`, and `events`. Live messages can omit some envelope fields depending on message type/context, so `video_1.py` fills harmless defaults before parsing.

Do not describe `WebsocketResponse` as a strict schema guarantee for every future Coinbase message. Coinbase says new message types can be added and clients should ignore unsupported messages. The script follows that spirit by skipping messages it cannot parse cleanly.

### Auth And API Keys

For public ticker data, no API key is needed.

For the `user` channel and real order placement, credentials are needed:

```bash
COINBASE_API_KEY='organizations/{org_id}/apiKeys/{key_id}'
COINBASE_API_SECRET='-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n'
```

The API secret is an EC private key. The newline characters matter. If sourcing from a shell file, quote the secret because the PEM header contains spaces.

Safe permission guidance:

- Use `view` for reading/watching account and order data.
- Add `trade` only if placing or canceling orders.
- Do not enable transfer permissions for this tutorial.

### Real Order Demo

The real-order switch is:

```python
PLACE_REAL_MARKET_BUY = False
```

Only set it to `True` for the stronger live-fill take.

When set to `True`, the script places a real market buy:

```python
REAL_BUY_PRODUCT_ID = "BTC-USDC"
REAL_BUY_QUOTE_SIZE = "10"
```

The output may show multiple updates for the same order:

```text
PENDING
OPEN
OPEN with cumulative_quantity
FILLED
FILLED again
```

That is acceptable and educational. Raw event streams can send multiple updates as state changes or repeats. Video 2 turns this into a cleaner wrapper helper that waits for the fill and filters by order ID.

### Sequence Numbers And Reliability

Coinbase WebSocket messages generally include sequence numbers. Sequence gaps can indicate dropped messages, and out-of-order messages are possible in real systems. This video does not implement sequence-gap recovery because it is not building an order book or a production market-making system.

Safe narration:

```text
For a beginner ticker and user-event demo, printing messages is enough. For production trading systems, especially order-book logic, you need sequence checks and state recovery.
```

### Should Video 1 Show AWS, Mac Mini, Codex Automations, Or Cron?

No. Keep Video 1 local.

Mention deployment only as a teaser:

```text
If this were going to run 24/7, I would run it as a long-running Python process with reconnect and logging. That is a later video.
```

Do not show:

- AWS EC2 setup
- Lambda
- Mac mini/OpenClaw
- Codex automations
- cron

Reason:

- WebSocket listeners are long-running processes.
- Cron is for scheduled jobs, not keeping a socket open.
- Lambda has a maximum invocation timeout and is the wrong shape for persistent sockets.
- Deployment would distract from the first video's core concept.

Codex can be shown lightly only as an explainer, not as a runtime:

```text
Explain this Coinbase WebSocket callback in beginner language. Keep the key point: REST asks for data, WebSocket receives pushed events.
```

Save actual vibe-coding for Video 2, where the wrapper and tests are the story.

## Pre-Filming Setup

Have open:

- Cursor with `video_1.py`
- Terminal in `/Users/rhettre/Github/coinbase/coinbase-advancedtrade-python`
- `.env.video`, with values hidden or placeholders
- Coinbase Developer Platform API key page
- Coinbase Advanced Trade page for `BTC-USDC`
- Optional Coinbase docs tabs:
  - WebSocket overview
  - WebSocket channels
  - SDK WebSocket guide

Terminal setup:

```bash
cd /Users/rhettre/Github/coinbase/coinbase-advancedtrade-python
source .venv/bin/activate
set -a
source .env.video
set +a
```

If using Cursor Run/Debug instead of terminal, make sure Cursor's Python process has the same environment variables. The simplest filming path is terminal execution.

Sanity checks:

```bash
.venv/bin/python -m py_compile video_1.py
.venv/bin/python -m unittest discover -s coinbase_advanced_trader/tests
```

Recommended safe switch before first take:

```python
PLACE_REAL_MARKET_BUY = False
```

For the stronger take:

```python
PLACE_REAL_MARKET_BUY = True
REAL_BUY_QUOTE_SIZE = "10"
USER_CHANNEL_SECONDS = 20
```

Use `USER_CHANNEL_SECONDS = 45` if doing manual place/cancel, because you need time to switch to Coinbase Advanced.

## Code Snippets To Show

These are the parts worth showing on screen. Do not scroll through every line.

### Imports

```python
from coinbase.rest import RESTClient
from coinbase.websocket import WSClient, WSUserClient, WebsocketResponse
```

Scriptwriter context:

- `RESTClient` places the optional real order.
- `WSClient` watches public market data.
- `WSUserClient` watches authenticated account/order events.
- `WebsocketResponse` parses raw JSON into easier Python objects.

### Filming Switches

```python
PUBLIC_PRODUCTS = ["BTC-USDC", "ETH-USDC"]
PUBLIC_SECONDS = 12

USER_PRODUCTS = ["BTC-USDC"]
USER_CHANNEL_SECONDS = 45

PLACE_REAL_MARKET_BUY = False
REAL_BUY_PRODUCT_ID = "BTC-USDC"
REAL_BUY_QUOTE_SIZE = "10"
```

Scriptwriter context:

- Public ticker products are safe: no auth, no trading.
- User products are private: require credentials.
- The real buy flag protects against accidental live orders.

### Parser Helper

```python
def parse_ws_message(raw_message: str) -> Optional[WebsocketResponse]:
    try:
        message_dict = json.loads(raw_message)
    except json.JSONDecodeError:
        print("Received a non-JSON message:", raw_message)
        return None

    if "channel" not in message_dict:
        return None

    if "events" not in message_dict:
        return None

    message_dict.setdefault("client_id", "")
    message_dict.setdefault("timestamp", "")
    message_dict.setdefault("sequence_num", 0)

    try:
        return WebsocketResponse(copy.deepcopy(message_dict))
    except Exception as error:
        print(f"Skipping unsupported WebSocket message: {error}")
        return None
```

Scriptwriter context:

- Raw callback input is JSON text.
- `json.loads` converts text to a dict.
- `WebsocketResponse` converts dicts to SDK response objects.
- Defaults are added because live messages may omit envelope fields.
- Unsupported messages are skipped so the demo keeps running.

Suggested line:

```text
This helper is not trading logic. It is a teaching helper that turns raw WebSocket JSON into something we can explain on camera.
```

### Public Ticker Stream

```python
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
```

Scriptwriter context:

- The callback is the heart of the demo.
- `ws_client.open()` opens the socket.
- `ws_client.ticker(...)` subscribes to live ticker events.
- `ws_client.heartbeats()` subscribes to heartbeat messages.
- `sleep_with_exception_check(...)` keeps the connection open for a bounded filming window and surfaces background errors.
- `finally: ws_client.close()` avoids leaving a socket open after the segment.

Suggested line:

```text
The callback is the mental model. Coinbase sends a message, and this function runs.
```

### WebsocketResponse Walkthrough

```python
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
```

Scriptwriter context:

- This is intentionally fake data to slow down and explain structure without relying on a live stream.
- It shows how `response.events[0].tickers[0].price` becomes accessible.

Suggested line:

```text
This is the same shape as the live message, but frozen so we can inspect it calmly.
```

### Trader Transport Map

```python
print("Vol-targeted trend: REST daily candles build the signal.")
print("Take-profit automation: REST places orders; WebSocket confirms fills.")
print("24/7 bot: WebSocket logs account events; REST recovers reference state.")
print("Market making: level2/trades/user streams are advanced, not Video 1.")
```

Scriptwriter context:

- This bridge prevents viewers from thinking every strategy needs millisecond WebSockets.
- It sets up Video 2 and Video 3 without expanding Video 1 too much.

Suggested line:

```text
Different jobs need different transports. A slow trend signal does not need a live order book; live fills do benefit from the user stream.
```

### Authenticated User Channel

```python
user_ws = WSUserClient(
    api_key=api_key,
    api_secret=api_secret,
    on_message=on_message,
)

user_ws.open()
try:
    user_ws.heartbeats()
    user_ws.user(USER_PRODUCTS)
    ...
finally:
    user_ws.close()
```

Scriptwriter context:

- `WSUserClient` is the private/authenticated WebSocket client.
- `heartbeats` still matter here.
- `user(USER_PRODUCTS)` subscribes to order updates for the authenticated user.

### User Event Printer

```python
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
```

Scriptwriter context:

- The important fields are:
  - `order_id`: identifies the order
  - `product_id`: market/product
  - `status`: lifecycle state
  - `order_side`: buy or sell
  - `cumulative_quantity`: filled base asset amount so far
  - `avg_price`: average fill price when available

Safe narration:

```text
This lets the script react to account-specific order changes, like pending, open, filled, or cancelled updates.
```

Avoid saying:

```text
Every order will always move through exactly these statuses in exactly this order.
```

### Optional Real Market Buy

```python
if PLACE_REAL_MARKET_BUY:
    print("\nPlacing a real market buy. This spends real money.")
    rest_client = RESTClient(api_key=api_key, api_secret=api_secret)
    order_response = rest_client.market_order_buy(
        client_order_id=uuid.uuid4().hex,
        product_id=REAL_BUY_PRODUCT_ID,
        quote_size=REAL_BUY_QUOTE_SIZE,
    )
    print("REST order response:")
    print(json.dumps(response_to_dict(order_response), indent=2))
```

Scriptwriter context:

- The order itself is placed through REST.
- The fill/update is observed through WebSocket.
- This is the cleanest demonstration of REST and WebSocket working together.

Suggested line:

```text
REST sends the order. WebSocket tells us what happened to it.
```

## Persuasion-Forward Demo Script

Use this as the main spoken pass when you want the tutorial to feel more
urgent and valuable. It keeps the technical accuracy from the runbook, but
puts the viewer's "why should I care?" question at the front and the back.

### Opening Hook

Screen:

- Terminal already printing live BTC/ETH ticker lines.
- Let the prices and heartbeats move for a few seconds before explaining
  anything.

Say:

> If you have only used the REST API, you eventually run into the same
> awkward question: how often should my script ask Coinbase if something
> changed?
>
> Every second? Every five seconds? What if my order fills between those
> checks? What if I am wasting requests just to learn that nothing happened?
>
> That is the problem this video solves. REST is great when I need a snapshot
> or when I need to send a command, like placing an order. But live trading
> workflows need something REST does not naturally give me: Coinbase telling
> my script the moment something changes.
>
> That is what you are seeing on screen. This is not a loop calling
> get_product over and over. This script opens a WebSocket, subscribes to BTC
> and ETH ticker updates, and Coinbase pushes messages into Python as the
> market moves.

Then:

> By the end of this video, you will have the foundation for event-driven
> Coinbase automation: live public prices, parsed WebSocket messages,
> heartbeats so the stream does not silently go quiet, and an authenticated
> user channel that can show your own order updates in real time.
>
> This is not a profit bot. This is the plumbing that lets a serious script
> react to reality instead of guessing with a polling loop.

### Setup And Promise

Screen:

- `video_1.py` open in Cursor.
- Terminal in `/Users/rhettre/Github/coinbase/coinbase-advancedtrade-python`.

Say:

> You need Python 3, the official Coinbase Advanced Trade Python SDK, and a
> terminal. Public price data does not require an API key, so we can start
> safely.
>
> For the private user stream, you need a CDP API key. View permission is
> enough to watch account and order data. Add trade only if you are going to
> place or cancel a tiny real order on camera. Transfer permission is not
> needed for this tutorial.

### Mental Model

Screen:

- Highlight `on_message` in `demo_public_ticker_stream()`.
- Highlight `WSClient(on_message=on_message)`.

Say:

> The callback is the star of the whole lesson. With REST, my script asks
> Coinbase a question and gets one answer back. With WebSocket, my script
> opens a line, subscribes to the events it cares about, and then Coinbase
> talks when something happens.
>
> That means this function runs every time a message arrives. Price update?
> This function runs. Heartbeat? This function runs. Later, when my own order
> changes status, the user-channel callback runs too.

Then:

> This is the value that was missing from a pure REST workflow. REST can tell
> me the current state when I ask. WebSocket can turn state changes into
> triggers.

### Public Ticker And Heartbeats

Screen:

- Highlight these lines:

```python
PUBLIC_PRODUCTS = ["BTC-USDC", "ETH-USDC"]
PUBLIC_SECONDS = 12

WSClient(on_message=on_message)
ws_client.ticker(PUBLIC_PRODUCTS)
ws_client.heartbeats()
ws_client.sleep_with_exception_check(PUBLIC_SECONDS)
```

Say:

> We start with the public ticker because it is the cleanest first win: no
> key, no account access, no trade permission. I subscribe to BTC and ETH,
> then I also subscribe to heartbeats.
>
> Heartbeats are not price data. They are a regular health signal from
> Coinbase. Coinbase documents that quiet channels can close after a short
> stretch with no updates, so heartbeats are a good habit even in beginner
> scripts.

Run the script.

Say:

> Now the terminal is printing price, best bid, and best ask as Coinbase
> pushes ticker updates into the callback. I am not asking, "what is the price
> now?" in a loop. Coinbase is sending the update when the feed has something
> to say.

If the terminal prints `BTC-USD` or `ETH-USD` after subscribing to
`BTC-USDC` or `ETH-USDC`, say:

> If you notice BTC-USD here, that is expected. Coinbase has a product-ID
> nuance where most public USDC subscriptions return the corresponding USD
> market data. For the private user channel, I keep BTC-USDC because that is
> the product I am watching for order events.

If nothing prints, say:

> If your terminal stays quiet, check internet access, firewall rules, and
> whether the script is still running. For the public ticker, an API key is
> not the issue because this channel is public.

### Parse Raw Messages Into Friendly Objects

Screen:

- Highlight `parse_ws_message(...)`.
- Highlight `json.loads`.
- Highlight `WebsocketResponse`.
- Then show the fake message walkthrough.

Say:

> The callback receives raw JSON text. Raw JSON is accurate, but it is noisy
> when you are learning and annoying when you are trying to build a clean
> workflow.
>
> This helper uses json.loads to turn the text into a Python dictionary, then
> WebsocketResponse from the official SDK turns the message into an object I
> can read with normal fields.

Point at:

```python
response.channel
response.events[0].tickers[0].price
ticker.product_id
ticker.best_bid
ticker.best_ask
```

Say:

> This is the same reason we eventually build a wrapper. The low-level API
> gives us the real data, but beginners and workflow code do better when the
> shape is easier to consume.

Optional technical detail:

> The helper also fills harmless envelope defaults for tutorial parsing and
> skips message types this demo does not support. Coinbase can add message
> types over time, so a real client should ignore unsupported messages instead
> of crashing.

### REST Versus WebSocket For Real Trader Workflows

Screen:

- Show `demo_trader_transport_map()` output.

Say:

> This is where people get the wrong takeaway if we are not careful.
> WebSockets are not "better than REST" in every situation. They solve a
> different problem.
>
> Use REST for snapshots and commands: daily candles, account snapshots,
> placing orders, cancelling orders, and rebuilding state after a hiccup.
>
> Use WebSocket when timing matters: live ticker updates, fills, cancels, and
> your own order status changes.

Then:

> That is the practical value. A REST-only script has to keep asking, "did it
> fill yet?" A WebSocket script can say, "tell me when it fills."

Production caveat:

> For this beginner demo, printing messages is enough. If you later build an
> order book, market maker, or 24/7 trading process, you need sequence checks,
> reconnects, logging, and REST recovery. This video is the foundation, not
> the whole production system.

### Add API Keys Safely

Screen:

- `.env.video` with values blurred or fake.
- Show variable names only.

Say:

> Public prices were safe because they did not need credentials. My private
> order updates do need credentials, because Coinbase has to know whose orders
> to send.
>
> Keep the key and secret in environment variables. Do not hardcode them in
> the Python file, and do not show real values on camera.

Show:

```bash
COINBASE_API_KEY='organizations/{org_id}/apiKeys/{key_id}'
COINBASE_API_SECRET='-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n'
```

Say:

> Quote the secret so the newline characters stay intact. If that private key
> gets mangled, authentication fails even though the code looks right.
>
> For permissions, use the narrowest key that supports the demo. View is
> enough for watching account and order data. Trade is needed only if I place
> or cancel an order. Transfer permission is not needed here.

### Watch Private Order Updates

Screen:

- Highlight:

```python
WSUserClient(api_key=api_key, api_secret=api_secret, on_message=on_message)
user_ws.heartbeats()
user_ws.user(USER_PRODUCTS)
```

Say:

> Now we switch from public market data to the authenticated user channel.
> This stream is account-specific. It can report order updates for the
> authenticated user.
>
> The important fields for a beginner bot are order_id, product_id, status,
> order_side, cumulative_quantity, and avg_price.

Screen:

- Terminal printing user events.

Say:

> This is the moment REST alone was not giving us cleanly. When an order
> changes from pending to open, or open to filled, I do not want to keep
> polling and hoping I picked the right interval. I want Coinbase to push the
> event into the script.

If no user events appear:

> If nothing appears here, make sure the action is on the same product, the
> key has view permission, and the terminal process actually loaded the
> environment variables.

### Optional Real Market Buy

Use only for the stronger take.

Screen:

- Highlight:

```python
PLACE_REAL_MARKET_BUY = True
REAL_BUY_PRODUCT_ID = "BTC-USDC"
REAL_BUY_QUOTE_SIZE = "10"
```

Say before running:

> This flag places a real market buy. I am using a tiny quote size, but it is
> still real money. Leave this false unless you are intentionally filming the
> live-fill version.

After the REST response prints:

> This response came from REST. REST is still doing exactly what it is good at:
> sending a command to Coinbase and getting an order response back.

When the WebSocket events print:

> Now the user WebSocket is doing what REST does not do by itself: reporting
> the order lifecycle as events. Pending, open, filled, and sometimes repeated
> updates for the same order. Raw event streams can be chatty, and that is
> normal.

Then:

> The big idea is not "market buy equals strategy." The big idea is that the
> script can now see the live fill data it needs: the actual filled size and
> the average fill price.

### Common Mistakes

Say:

> The first mistake is treating WebSockets like optional decoration. If your
> script needs to react to fills, cancels, or account events, polling REST can
> work, but it is clunkier and easier to get wrong.
>
> The second mistake is skipping heartbeats. Quiet channels can close after a
> short stretch, and heartbeats give you a regular "still alive" signal.
>
> The third mistake is getting stuck on BTC-USDC versus BTC-USD in public
> feeds. Seeing BTC-USD on the public ticker is expected Coinbase behavior.
> Keep BTC-USDC on the user channel for the order demo.
>
> The fourth mistake is breaking the API secret. If the EC private key is not
> quoted and the newline characters get mangled, authentication fails.

### Closing

Screen:

- Terminal with live ticker output and, if available, user-channel order events.
- Then briefly show `demo_trader_transport_map()`.

Say:

> Here is why this matters. REST can tell your script what the state is when
> you ask. WebSocket can tell your script when the state changes.
>
> That difference is the line between a script that keeps asking "did anything
> happen yet?" and a script that can react when Coinbase pushes the event.

Then:

> In this demo, we streamed live BTC and ETH prices, parsed raw WebSocket JSON
> into friendlier SDK objects, used heartbeats as a connection health signal,
> and watched the authenticated user channel report order changes in real
> time.
>
> That is the value the viewer was not getting from REST alone: live triggers.
> Cleaner fill detection. Less polling. A better foundation for automation.

Bridge to Video 2:

> The official SDK gives us the building blocks. The wrapper's job is to turn
> those building blocks into beginner-friendly workflows: watch prices, wait
> for a fill, and place a follow-up order using the real filled size and
> average fill price.
>
> That is what we build next. We take this low-level WebSocket power and
> package it into helpers people can actually use without thinking about every
> message shape, heartbeat, and callback.

Final line:

> REST sends the command. WebSocket reports what happened. The wrapper turns
> that into a workflow.

## Full Segment Script

Use this as a structured speaking outline. It is intentionally more precise than a teleprompter script.

### Segment 0: Cold Open

Screen:

- Terminal already running public ticker output.
- BTC/ETH prices scrolling.

Say:

```text
This is Coinbase pushing live price updates into a Python script. I am not calling get_product over and over in a loop. The script opens a WebSocket, subscribes to ticker updates, and Coinbase sends messages whenever the feed has something to tell us.
```

Then:

```text
That is the main difference from REST. With REST, my script asks Coinbase a question. With WebSockets, Coinbase can push events into my script as they happen.
```

### Segment 1: Public Ticker

Screen:

- `demo_public_ticker_stream()`
- Highlight `WSClient(on_message=on_message)`

Say:

```text
This callback is the most important line in the whole video. Every time Coinbase sends a message, the SDK passes that message into this function.
```

Point at:

```python
ws_client.ticker(PUBLIC_PRODUCTS)
```

Say:

```text
This subscribes to ticker updates for BTC and ETH. This part does not need an API key, because public market data is public.
```

Point at:

```python
ws_client.heartbeats()
```

Say:

```text
Heartbeats are a keepalive and health signal. Coinbase documents that quiet channels can close if no updates are sent for a while, so subscribing to heartbeats is a good habit.
```

If the terminal prints `BTC-USD` instead of `BTC-USDC`, say:

```text
Coinbase has a small product-ID nuance here: most public USDC subscriptions can return the corresponding USD market data. For the private user-channel order events, I keep BTC-USDC because that is the product I am watching or trading.
```

### Segment 2: Parsing With WebsocketResponse

Screen:

- `demo_parse_one_message_without_a_websocket()`

Say:

```text
Raw JSON is useful, but it is noisy on camera and annoying for beginners. The official SDK gives us WebsocketResponse, which turns the raw message into Python objects.
```

Point at:

```python
response.channel
response.events
ticker.product_id
ticker.price
```

Say:

```text
Once the message is parsed, I can work with normal Python attributes instead of digging through a raw JSON dictionary every time.
```

Technical caveat if needed:

```text
The helper also skips message types this demo does not support. Coinbase can add message types over time, so robust clients should ignore things they do not understand.
```

### Segment 3: Transport Map

Screen:

- `demo_trader_transport_map()`

Say:

```text
This does not mean every trading idea needs a high-frequency WebSocket feed. A slow volatility-targeted trend strategy can use REST daily candles. But when I care about live order status, fills, cancels, or account events, WebSockets become much more useful.
```

Then:

```text
Market making and order-book strategies need deeper channels like level2 and a lot more risk plumbing. That is not this beginner demo.
```

### Segment 4: API Keys And Private User Channel

Screen:

- `.env.video`, with fake or blurred values

Say:

```text
Public price data did not need credentials. My private order events do. I keep the API key and private key in environment variables instead of hardcoding them into the script.
```

Permission line:

```text
For watching account and order data, use view permission. Add trade only if you are actually placing or canceling orders. You do not need transfer permission for this tutorial.
```

Important safety line:

```text
Do not show real secrets on camera, and if you enable trade permission for a demo key, disable or delete that key after filming.
```

### Segment 5: Authenticated User Channel

Screen:

- `demo_authenticated_user_channel()`

Point at:

```python
user_ws = WSUserClient(...)
user_ws.user(USER_PRODUCTS)
```

Say:

```text
This is the authenticated user channel. Instead of public market data, this stream sends messages related to my orders.
```

Point at printed fields:

```python
order.order_id
order.status
order.cumulative_quantity
order.avg_price
```

Say:

```text
These are exactly the fields a beginner bot wants to see: what order changed, what product it was for, whether it is pending, open, filled, or cancelled, how much has filled, and the average fill price when Coinbase has one.
```

### Segment 6A: Safer Manual Order Event

Use if `PLACE_REAL_MARKET_BUY=False`.

Screen:

- Terminal running the user channel.
- Coinbase Advanced Trade in browser.

Say:

```text
For the safer version, I am not letting the script place the order. I will manually place and cancel a tiny or far-away limit order in Coinbase, and the WebSocket should report the account event back to the script.
```

Then trigger the event manually.

Say:

```text
The important part is that the Python script did not poll Coinbase asking, did anything happen yet? Coinbase pushed the event into the script.
```

### Segment 6B: Stronger Real Market Buy

Use only if `PLACE_REAL_MARKET_BUY=True`.

Screen:

- `PLACE_REAL_MARKET_BUY=True`
- Terminal output

Say before running:

```text
This flag places a real market buy. I am using a tiny quote size, but this is still real money.
```

After REST order response:

```text
This response came from REST. REST placed the order and returned the order ID.
```

When WebSocket events print:

```text
Now the WebSocket user channel is reporting the order lifecycle live. Pending, open, partially filled, filled. This is the part that unlocks automation without polling in a loop.
```

If duplicate `FILLED` events print:

```text
Notice we may see more than one update for the same order. Raw event streams are chatty. In the next video, the wrapper filters this into a cleaner wait-for-fill helper.
```

### Segment 7: Bridge To Video 2

Say:

```text
Now we know how to connect to the official SDK, watch public prices, parse messages, and see private order updates. In the next video, I am going to turn that low-level WebSocket power into wrapper functions people actually want to use: watch prices, wait for a fill, and place a follow-up order from the real filled size and average fill price.
```

End thought:

```text
The official SDK gives us the building blocks. The wrapper's job is to package useful workflows without pretending trading is risk-free.
```

## Example Output To Reference

Public ticker output may look like:

```text
BTC-USD  price=80438.09 bid=80438.08 ask=80438.09
ETH-USD  price=2387.50  bid=2387.50  ask=2387.56
heartbeat #238227 at 2026-05-04 04:05:19...
```

User-channel real order output may look like:

```text
REST order response:
{
  "success": true,
  "success_response": {
    "order_id": "...",
    "product_id": "BTC-USDC",
    "side": "BUY",
    "client_order_id": "..."
  }
}

user event order_id=... product=BTC-USDC status=PENDING side=BUY filled=0 avg_price=0
user event order_id=... product=BTC-USDC status=OPEN side=BUY filled=0 avg_price=0
user event order_id=... product=BTC-USDC status=OPEN side=BUY filled=0.00012287 avg_price=80406.95
user event order_id=... product=BTC-USDC status=FILLED side=BUY filled=0.00012287 avg_price=80406.95
```

Technical interpretation:

- REST successfully placed the order.
- WebSocket reported the order lifecycle.
- `cumulative_quantity` is the filled base quantity.
- `avg_price` is the average fill price when available.
- Multiple events for the same order can appear.

## Common Mistakes To Avoid In Narration

Do not say:

```text
WebSockets are always better than REST.
```

Say:

```text
They solve different problems. REST is great for snapshots and commands; WebSockets are great for pushed events.
```

Do not say:

```text
Heartbeats guarantee the connection stays open forever.
```

Say:

```text
Heartbeats help keep quiet subscriptions alive and give us a health signal, but production code still needs reconnect logic.
```

Do not say:

```text
This is a profitable bot.
```

Say:

```text
This is infrastructure for reacting to market and order events. Trading strategy and risk controls are separate.
```

Do not say:

```text
The user channel replaces all REST account/order calls.
```

Say:

```text
The user channel is excellent for live updates. REST is still useful for placing orders, fetching snapshots, and reconciling state.
```

Do not say:

```text
This script can run 24/7 as-is.
```

Say:

```text
The connection can be kept open as a long-running process, but a production bot needs logging, reconnects, state recovery, and a process manager.
```

Do not say:

```text
Cron runs the WebSocket bot.
```

Say:

```text
Cron is for scheduled jobs. A WebSocket listener should be a long-running process managed by systemd, Docker, launchd, or similar tooling.
```

## Optional B-Roll / On-Screen Notes

Potential on-screen captions:

```text
REST: request -> response
WebSocket: subscribe -> pushed events
Public ticker: no API key
User channel: API key required
Heartbeats: keep quiet subscriptions alive
REST places the order. WebSocket reports what happened.
```

Potential diagram:

```text
REST order request
Python script  ----------------------> Coinbase
              <----------------------  order_id

WebSocket user channel
Python script  <----------------------  PENDING / OPEN / FILLED events
```

Potential safety lower-third:

```text
Real order placement is disabled by default. Enable only for tiny demo trades.
```

## Code Changes Relevant To Video 1

The demo file is gitignored and local:

```text
video_1.py
```

Relevant modifications made for filming:

1. Added `parse_ws_message(...)` to convert raw callback JSON into `WebsocketResponse` and skip unsupported messages safely.
2. Added envelope defaults for `client_id`, `timestamp`, and `sequence_num` before parsing.
3. Added a public ticker segment using `WSClient`.
4. Added a static parsing walkthrough so the scriptwriter can explain `WebsocketResponse` without waiting on live messages.
5. Added a trader transport map that connects Video 1 to Videos 2 and 3.
6. Added authenticated `WSUserClient` user-channel demo.
7. Added the optional real market buy guarded by `PLACE_REAL_MARKET_BUY`.
8. Added `response_to_dict(...)` so official SDK REST response objects can be printed as JSON-like output.

No official SDK source files were changed for Video 1. The official SDK repo is used as the reference.

## Suggested Final Video Structure

Approximate timing:

```text
0:00 - 0:25  Live hook with ticker output
0:25 - 1:45  REST vs WebSocket mental model
1:45 - 3:30  Public ticker code
3:30 - 4:30  Heartbeats and product-ID nuance
4:30 - 6:00  WebsocketResponse parsing
6:00 - 7:00  Trader transport map
7:00 - 8:30  API key and private user channel setup
8:30 - 10:30 Authenticated user events / optional real buy
10:30 - 11:15 Bridge to wrapper automation in Video 2
```

## Scriptwriter FAQ

### Is this using Rhett's wrapper?

No. Video 1 is the official SDK. Rhett's wrapper is discussed only as the next step.

### Does public ticker require auth?

No. The public ticker demo can run without API keys.

### Does the user channel require auth?

Yes. The `user` channel is private and requires credentials.

### Why subscribe to heartbeats?

Coinbase documents that most channels can close after 60-90 seconds without updates. Heartbeats help keep subscriptions open and provide a regular health signal.

### Why does BTC-USDC print as BTC-USD?

Coinbase documents that most public `-USDC` subscriptions return corresponding `-USD` market data. `-USDC` product IDs are specifically available on the user channel.

### Is the real market buy required?

No. The safer demo is manual place/cancel. The real market buy is a stronger moment, but it is optional and spends real money.

### Is this a 24/7 bot?

No. It is a bounded teaching script. A 24/7 bot needs process management, logging, reconnects, and state reconciliation.

### Can this be done with cron?

Not the WebSocket listener. Cron is for scheduled commands. A WebSocket listener should stay running.

### Should we show Codex?

Only briefly as an explainer if desired. Save real vibe-coding for Video 2.

## Official Source Context For Scriptwriter

This section brings the relevant official-documentation context into the script packet itself. It is paraphrased for production use, not copied wholesale. The source links are preserved for provenance, but the scriptwriter should not need to open them.

Captured from official Coinbase documentation on May 4, 2026.

### Source 1: Coinbase Advanced Trade API / SDK Overview

Source:

```text
https://docs.cdp.coinbase.com/advanced-trade/docs/sdk-overview
```

Current redirect observed:

```text
https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/overview
```

Relevant context:

- Coinbase describes Advanced Trade API as supporting programmatic trading and order management.
- The platform supports both REST API access and WebSocket protocol access.
- REST and WebSocket are not competing replacements in Coinbase's docs; they are both part of the Advanced Trade API surface.
- Coinbase positions WebSockets as the protocol for real-time market data.
- Coinbase lists official SDKs, including the official Python SDK used in Video 1.
- Advanced Trade is the advanced trading platform for buying, selling, and trading digital assets across supported pairs.

Script-safe interpretation:

```text
Coinbase Advanced Trade gives developers both REST and WebSocket interfaces. In this video, REST is used for the optional order request, while WebSocket is used to receive live pushed updates.
```

Avoid:

```text
The WebSocket SDK replaces the REST SDK.
```

Better:

```text
The official SDK gives us both styles of interaction: REST for commands and snapshots, WebSocket for live events.
```

### Source 2: Coinbase Advanced Trade WebSocket Overview

Source:

```text
https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview
```

Relevant context:

- Coinbase describes the Advanced Trade WebSocket feed as publicly available for real-time market data related to orders and trades.
- Coinbase documents two production WebSocket endpoints:
  - Market Data Endpoint: `wss://advanced-trade-ws.coinbase.com`
  - User Order Data Endpoint: `wss://advanced-trade-ws-user.coinbase.com`
- The market-data endpoint is the traditional real-time feed for orders and trades; Coinbase says most channels are now available without authentication.
- The user-order endpoint provides updates for the authenticated user's orders.
- Coinbase says the WebSocket protocol uses JSON messages.
- Messages have a `type` attribute so clients can decide how to handle them.
- Coinbase warns that new message types may be added over time and clients should ignore unsupported message types.
- After opening a WebSocket connection, the client must subscribe to a channel/product combination. Coinbase says a subscription message is mandatory and the server can disconnect clients that do not subscribe quickly.
- Coinbase says each subscription message can subscribe to one channel. A client can subscribe to multiple channels by sending separate subscription messages.
- Authenticated subscription messages include a JWT.
- Coinbase says JWTs expire after two minutes, so new JWTs must be generated for new authenticated WebSocket messages.
- Coinbase documents unsubscribe messages as similar in structure to subscribe messages.
- Coinbase describes sequence numbers as increasing values. Gaps can mean messages were dropped, and lower sequence numbers may indicate out-of-order messages. Production systems need to handle this when state correctness matters.

Script-safe interpretation:

```text
In this beginner demo, the official SDK hides most endpoint and JWT mechanics. But under the hood, we still open a WebSocket connection, send subscription messages, and receive JSON events.
```

Important caveat for the script:

```text
Because Coinbase can add message types and because sequence gaps can happen, production systems should not assume this print-only demo is complete reliability logic.
```

Use this line if discussing `parse_ws_message`:

```text
The helper skips messages it does not understand because Coinbase explicitly expects clients to tolerate unsupported message types.
```

Use this line if discussing production:

```text
For a production book or trading-state engine, sequence numbers and REST recovery matter. For this beginner demo, we are only printing ticker and user-order events.
```

### Source 3: Coinbase Advanced Trade WebSocket Channels

Source:

```text
https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-channels
```

Relevant channel list:

- `heartbeats`: public; sends server pings and helps keep connections/subscriptions open.
- `candles`: public; sends real-time updates for product candles.
- `status`: public; sends product/currency information on an interval.
- `ticker`: public; sends real-time price updates when matches happen.
- `ticker_batch`: public; sends price updates every 5000 milliseconds.
- `level2`: public; used for order-book updates and maintaining a book snapshot.
- `market_trades`: public; sends real-time updates when market trades happen.
- `user`: authenticated; sends messages that include the authenticated user.
- `futures_balance_summary`: authenticated; sends updates when a user's futures balance changes.

Heartbeat context:

- Coinbase says most channels may close within 60-90 seconds if no updates are sent.
- Coinbase recommends subscribing to heartbeats to keep subscriptions open when updates are sparse.
- Heartbeat messages arrive regularly and include a heartbeat counter.
- The heartbeat counter can help verify message continuity in the heartbeat stream.
- Heartbeats are especially useful when subscribed products are quiet or illiquid.

Ticker context:

- The ticker channel provides real-time price updates when matches happen.
- Coinbase batches ticker updates in cascading-match situations to reduce bandwidth.
- Ticker messages include fields such as product ID, price, best bid, and best ask.
- The public ticker is enough to demonstrate "Coinbase pushes price events into my callback."

User-channel context:

- The `user` channel is authenticated and sends account/order-related messages for the authenticated user.
- The channel can include order data such as order ID, product ID, side, status, average price, cumulative filled quantity, filled value, total fees, number of fills, limit price, and other fields.
- Documented order statuses include:
  - `PENDING`: order is not yet open
  - `OPEN`: order is waiting to be fully filled
  - `FILLED`: order is fully filled
  - `CANCEL_QUEUED`: cancellation has been queued
  - `CANCELLED`: order was cancelled
  - `EXPIRED`: time-limited order expired
  - `FAILED`: order could not be placed

Product-ID context:

- Coinbase documents a special `-USDC` behavior.
- Subscribing to `-USDC` products is only directly available on the `user` channel.
- Other channels return corresponding `-USD` market data for most `-USDC` subscriptions.
- `USDT-USDC` and `EURC-USDC` are documented exceptions available across all channels.

Script-safe interpretation:

```text
If the public ticker prints BTC-USD after subscribing to BTC-USDC, that is expected Coinbase behavior for most public channels. For the authenticated user channel, BTC-USDC remains the product ID for the order events.
```

Use this line when explaining heartbeats:

```text
Coinbase documents that quiet channels can close after a short period without updates, so we subscribe to heartbeats alongside the ticker and user streams.
```

Avoid:

```text
Heartbeats make disconnects impossible.
```

Better:

```text
Heartbeats help keep quiet subscriptions open and give us a health signal, but production code still needs reconnect and recovery logic.
```

### Source 4: Coinbase Advanced Trade WebSockets Guide

Source:

```text
https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/guides/websocket
```

Relevant context:

- Coinbase's WebSocket guide is a setup/authentication/subscription guide for Advanced Trade WebSockets.
- It describes the WebSocket API as providing real-time market data and user-specific order information.
- It identifies the same two endpoints:
  - public market-data endpoint for real-time market/order/trade updates
  - authenticated user-order endpoint for order status and active trade updates
- It explains that user-specific channels require JWT authentication.
- It says the JWT is generated using the API key and signing key.
- It says JWTs expire after two minutes.
- It shows authenticated user-channel subscription shape with:
  - `type: subscribe`
  - `channel: user`
  - `product_ids`
  - `jwt`
- It shows public ticker subscription shape without JWT.
- It groups channels into public and private categories:
  - public examples: ticker, ticker batch, market trades, status, level2, candles
  - private examples: user, futures balance summary

Script-safe interpretation:

```text
The official SDK handles the low-level JWT and subscription details for us. That is why our code can call user_ws.user([...]) instead of manually building JSON subscription messages.
```

Use this when explaining credentials:

```text
For private user data, Coinbase expects authentication using a CDP API key and signing key. In the SDK, we provide those as api_key and api_secret.
```

Use this when explaining public vs private:

```text
The ticker example is public. The user-channel example is private because it shows my account's order events.
```

### Source 5: Coinbase Get API Key Permissions Endpoint

Source:

```text
https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/data-api/get-api-key-permissions
```

Relevant context:

- Coinbase provides an endpoint for retrieving information about a CDP API key's permissions.
- The response includes boolean permission flags:
  - `can_view`
  - `can_trade`
  - `can_transfer`
  - `can_receive`
- `can_view` indicates whether the key has view permissions.
- `can_trade` indicates whether the key has trade permissions.
- `can_transfer` indicates whether the key can perform deposit/withdrawal style transfer actions.
- `can_receive` indicates whether the key can receive inbound payments.
- The response can include portfolio metadata such as portfolio UUID and portfolio type.
- The endpoint itself requires authorization using a JWT signed with the CDP API key secret.

Script-safe permission guidance:

```text
For a tutorial key, use the narrowest permissions that support the demo. View is enough for reading/watching. Trade is needed only if placing or canceling orders. Transfer permissions are not needed for this video.
```

Avoid:

```text
Just enable everything so the demo works.
```

Better:

```text
Use the minimum permissions needed for the exact demo, and remove or disable the key after filming if trade permission was enabled.
```

### Consolidated Fact Sheet

The scriptwriter can rely on these statements:

- Coinbase Advanced Trade supports both REST and WebSocket interfaces.
- The official Python SDK is an official Coinbase SDK for Advanced Trade.
- REST is useful for commands and snapshots, including placing the optional real order.
- WebSocket is useful for pushed real-time events.
- Coinbase has separate production WebSocket endpoints for market data and user order data.
- Public market-data channels can be used without API keys.
- The `ticker` channel is public and sends real-time price updates when matches occur.
- The `heartbeats` channel is public and helps keep quiet subscriptions open.
- Coinbase says most channels can close within 60-90 seconds if no updates are sent.
- The `user` channel is authenticated and sends user-specific order data.
- Private WebSocket subscriptions use JWT authentication generated from a CDP API key and signing key.
- JWTs expire after two minutes; the official SDK handles this for the demo's subscription calls.
- Coinbase can add new WebSocket message types; clients should ignore unsupported messages.
- Sequence numbers can reveal dropped or out-of-order messages; production stateful systems need to account for this.
- Public `-USDC` subscriptions generally map to corresponding `-USD` market data, while `-USDC` products are directly available on the `user` channel.
- API key permission concepts include view, trade, transfer, and receive.
- The tutorial does not require transfer permissions.
- A real market buy requires trade permission and spends real money.
- This video is not a trading strategy, profit guarantee, deployment guide, or production bot.

### Source Links Kept For Provenance

- Coinbase Advanced Trade SDK/API overview: https://docs.cdp.coinbase.com/advanced-trade/docs/sdk-overview
- Coinbase WebSocket overview: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview
- Coinbase WebSocket channels: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-channels
- Coinbase WebSocket setup/authentication guide: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/guides/websocket
- Coinbase API key permissions endpoint: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/data-api/get-api-key-permissions
