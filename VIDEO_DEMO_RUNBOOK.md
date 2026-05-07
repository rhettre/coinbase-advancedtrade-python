# Coinbase WebSocket Mini-Series Demo Runbook

This runbook is the filming guide for the three local demo scripts:

- `video_1.py`: official Coinbase SDK WebSocket tutorial
- `video_2.py`: Rhett wrapper workflow demos
- `video_3.py`: always-on bot and deployment shape

The core viewer takeaway across all three videos:

```text
REST asks Coinbase for state.
WebSocket lets Coinbase push live events into your script.
The wrapper should package useful workflows, not mirror every low-level channel.
```

Nothing in this series guarantees daily or weekly profits. The trader-friendly framing is risk-first automation: slow signals can use REST candles, live order state should use WebSockets, and real order placement must account for fees, slippage, position limits, and operational failure.

## Before Filming

Have these open:

- Cursor with the wrapper repo: `/Users/rhettre/Github/coinbase/coinbase-advancedtrade-python`
- Terminal in the wrapper repo
- `video_1.py`, `video_2.py`, `video_3.py`
- `VIDEO_DEMO_RUNBOOK.md`
- `.env.video`, with real values hidden or placeholder values on camera
- Coinbase Developer Platform / API key page
- Coinbase Advanced Trade page for `BTC-USDC`
- Optional docs tabs:
  - Coinbase Advanced Trade API endpoints
  - Coinbase WebSocket overview
  - Coinbase WebSocket channels
  - AWS Lambda timeout docs
  - AWS EC2 console

Security prep:

- Create a fresh API key named something like `YouTube Demo`.
- Use `view` permission for watching accounts/orders and reading products.
- Add `trade` only for takes where you place/cancel orders on camera.
- Do not enable transfer permissions for these demos.
- Do not show the real secret on camera.
- Delete or disable the demo key after filming if you enabled `trade`.

Local environment:

```bash
cd /Users/rhettre/Github/coinbase/coinbase-advancedtrade-python

# If .env.video uses KEY=value lines:
set -a
source .env.video
set +a

# Sanity checks:
.venv/bin/python -m py_compile video_1.py video_2.py video_3.py
.venv/bin/python -m unittest discover -s coinbase_advanced_trader/tests
```

Expected `.env.video` shape:

```bash
COINBASE_API_KEY='organizations/{org_id}/apiKeys/{key_id}'
COINBASE_API_SECRET='-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n'
```

Quote `COINBASE_API_SECRET` if you plan to `source .env.video` in a shell. The PEM header contains spaces, so an unquoted secret can be misread by the shell. The filming scripts can load `.env.video` directly, but quoting the value keeps both workflows safe.

Do not run package internals directly, for example:

```bash
python coinbase_advanced_trader/enhanced_rest_client.py
```

That file uses package-relative imports and is meant to be imported by scripts. Run `video_1.py`, `video_2.py`, `video_3.py`, or import the wrapper from a Python shell instead.

## Video 1: Official SDK WebSocket Tutorial

Working title:

```text
Coinbase Advanced Trade WebSocket API Tutorial | Official Python SDK
```

Big idea:

```text
REST is request/response. WebSocket is event-driven.
```

What to have open:

- `video_1.py`
- Terminal
- `.env.video`
- Coinbase Developer/API key page
- Coinbase Advanced Trade `BTC-USDC`
- Coinbase WebSocket docs, optional

Script switches:

```python
PLACE_REAL_MARKET_BUY = False
REAL_BUY_PRODUCT_ID = "BTC-USDC"
REAL_BUY_QUOTE_SIZE = "10"
```

Keep `PLACE_REAL_MARKET_BUY=False` for the first take. Only flip it to `True` for the stronger real-fill moment.

Demo flow:

1. Start with a live hook.

   Run:

   ```bash
   .venv/bin/python video_1.py
   ```

   Let the public ticker output scroll for a few seconds.

   Say:

   ```text
   This is not a loop calling get_product again and again. Coinbase is pushing ticker events into this script live.
   ```

2. Show `demo_public_ticker_stream()`.

   Point at:

   - `WSClient(on_message=on_message)`
   - `ws_client.ticker(PUBLIC_PRODUCTS)`
   - `ws_client.heartbeats()`
   - `sleep_with_exception_check(...)`

   Viewer beat:

   ```text
   The callback is the whole mental model. Every time Coinbase sends a message, this function runs.
   ```

3. Explain public data.

   Say:

   ```text
   Public market data is the friendly starting point. No key, no account access, no trading.
   ```

4. Explain `WebsocketResponse`.

   When the script reaches the parsing walkthrough, show:

   - `response.channel`
   - `response.events`
   - `ticker.product_id`
   - `ticker.price`

   Say:

   ```text
   Raw JSON is noisy. WebsocketResponse turns it into Python objects that are much easier to teach and debug.
   ```

5. Explain the trader transport map.

   This is the bridge into the rest of the series:

   ```text
   Volatility-targeted trend can use REST daily candles. Live fills and order updates belong on WebSockets. Market making needs even deeper WebSocket plumbing, so that is not the beginner demo.
   ```

6. Show `.env.video`.

   Do not show real secrets. Use placeholders or blur the values.

   Say:

   ```text
   For private account events, the user channel needs credentials. I keep those in environment variables, not directly in the Python file.
   ```

7. Show `demo_authenticated_user_channel()`.

   Point at:

   - `WSUserClient`
   - `user_ws.user(USER_PRODUCTS)`
   - printed fields: `order_id`, `status`, `cumulative_quantity`, `avg_price`

8. Trigger a user event.

   Safer option:

   - Leave `PLACE_REAL_MARKET_BUY=False`.
   - Run the script.
   - While it watches the user channel, manually place a far-away limit order in Coinbase Advanced.
   - Cancel it.
   - Let the script print the order update if Coinbase pushes it during the watch window.

   Stronger option:

   - Set `PLACE_REAL_MARKET_BUY=True`.
   - Keep `REAL_BUY_QUOTE_SIZE="10"` or another tiny amount.
   - Run the script.
   - Watch for the fill/update event.

   Say:

   ```text
   This is real money when the flag is true. Keep the default false until the exact take is ready.
   ```

9. End with the Video 2 bridge.

   Say:

   ```text
   Now that we can detect fills live, the next step is wrapping that into a beginner-friendly workflow.
   ```

Do not over-teach:

- Do not list every Coinbase WebSocket channel.
- Do not turn this into market making.
- Do not promise profit.

Video 1 ops questions:

- Do not show AWS in Video 1. Mention it only as a teaser: "A long-running WebSocket bot belongs on always-on compute, and that is Video 3."
- Do not show Mac mini/OpenClaw setup in Video 1. It is a valid always-on home-server option, but it distracts from the official SDK callback lesson.
- Do not show Codex automations as the runtime for a trading bot. Codex can help edit/explain code, but the production bot should run as a Python process under `systemd`, Docker, `launchd`, or another process manager.
- Do not use cron for a live WebSocket listener. Cron starts scheduled jobs; it does not keep one socket open. Cron is fine for scheduled REST scripts or maybe a watchdog check, but the WebSocket process itself should stay running.
- Coinbase documents that most channels can close within 60-90 seconds if there are no updates. Subscribing to `heartbeats` is the beginner-friendly fix.
- A WebSocket can be run 24/7 as a long-running process, but production code must expect disconnects, reconnect, resubscribe, and reconcile state through REST when needed.
- The official SDK defaults `retry=True`, and its retry path reconnects and resubscribes after unexpected connection closures. That is helpful, but it is not a complete production monitor by itself.
- The local `video_1.py` intentionally uses `sleep_with_exception_check(...)` for a bounded teaching segment. For a 24/7 bot, use `run_forever_with_exception_check()` or an outer process loop like `video_3.py`.
- If the public ticker prints `BTC-USD` even when you asked for `BTC-USDC`, use that as a teachable Coinbase product-ID nuance: Coinbase documents that most public `-USDC` subscriptions return the corresponding `-USD` data, while `-USDC` product IDs are specifically available on the user channel.

Optional script tweaks for Video 1:

- Set `PUBLIC_SECONDS = 6` for a tighter public ticker hook.
- Use `PUBLIC_PRODUCTS = ["BTC-USD", "ETH-USD"]` if you want the public output to match the visible product IDs exactly.
- Use `PUBLIC_PRODUCTS = ["BTC-USDC", "ETH-USDC"]` if you want to explain the Coinbase `-USDC`/`-USD` public-channel behavior.
- Set `USER_CHANNEL_SECONDS = 20` when using `PLACE_REAL_MARKET_BUY=True`, because fills usually arrive quickly and a shorter watch keeps the take snappy.
- Keep `USER_CHANNEL_SECONDS = 45` when using manual place/cancel, because you need time to switch to Coinbase Advanced and trigger the event.
- Add a temporary `ORDER_ID_TO_WATCH` print/filter only if the terminal becomes too noisy. Do not over-engineer this in Video 1; normalized filtering belongs in Video 2's wrapper.
- Set `verbose=True` on `WSClient` or `WSUserClient` only for a debugging cutaway. It is too noisy for the main tutorial.

Optional Codex/vibe-coding beat for Video 1:

Use Codex only as a quick explanatory sidekick, not as the star. A good on-camera prompt is:

```text
Explain this Coinbase WebSocket callback in beginner language. Keep the key point: REST asks for data, WebSocket receives pushed events.
```

Save deeper vibe coding for Video 2, where you can show the wrapper feature and tests.

## Video 2: Wrapper Workflows And Trader Use Case

Working title:

```text
I Added Live Order Automation to My Coinbase Python Wrapper
```

Big idea:

```text
The official SDK gives us the low-level power. The wrapper should package the workflows people actually want to use.
```

What to have open:

- `video_2.py`
- `coinbase_advanced_trader/enhanced_rest_client.py`
- `coinbase_advanced_trader/services/websocket_service.py`
- `coinbase_advanced_trader/services/strategy_planner_service.py`
- `coinbase_advanced_trader/tests/test_strategy_planner_service.py`
- README WebSocket section
- Terminal
- Coinbase Advanced `BTC-USDC`

Script switches:

```python
RUN_REAL_TAKE_PROFIT_DEMO = False
TAKE_PROFIT_PRODUCT_ID = "BTC-USDC"
TAKE_PROFIT_FIAT_AMOUNT = "10"
SELL_PRICE_MULTIPLIER = "1.05"
CANCEL_OPEN_ORDERS_AT_END = False
```

Keep real order placement off until the final take.

Demo flow:

1. Start with the design choice.

   Say:

   ```text
   I do not want my wrapper to copy every WebSocket channel one-for-one. Coinbase already maintains that in the official SDK. The wrapper should make common workflows easier.
   ```

2. Run the wrapper public price helper.

   Run:

   ```bash
   .venv/bin/python video_2.py
   ```

   First segment shows:

   ```python
   client.watch_prices(["BTC-USDC", "ETH-USDC"], seconds=10)
   ```

   Say:

   ```text
   This is the beginner-friendly version of the official SDK ticker stream from Video 1.
   ```

3. Show the conservative trader upgrade.

   The script calls:

   ```python
   client.build_volatility_targeted_trend_plan(
       product_id="BTC-USDC",
       quote_budget="100",
       lookback_days=120,
       momentum_days=30,
       target_annual_volatility="0.08"
   )
   ```

   Explain the fields:

   - `signal`: `BUY`, `REDUCE`, or `HOLD`
   - `trend_return`: recent momentum
   - `realized_annual_volatility`: 365-day crypto annualization
   - `exposure_fraction`: volatility-scaled sizing
   - `target_quote_notional`: dry-run target amount

   Say:

   ```text
   This is not a daily-profit bot. This is a dry-run plan: direction from trend, size from volatility, and no order placed yet.
   ```

4. Show where it lives.

   Open `strategy_planner_service.py`.

   Point at:

   - `VolatilityTargetedTrendPlan`
   - `build_volatility_targeted_trend_plan`
   - `get_public_candles`
   - `ANNUALIZATION_DAYS = Decimal("365")`

   Viewer beat:

   ```text
   This came from the research: trend and volatility targeting are much better first production candidates than pretending every day should be profitable.
   ```

5. Show normalized order events.

   Open `websocket_service.py`.

   Point at:

   - `OrderEvent`
   - `watch_order_events`
   - `wait_for_order_fill`
   - `place_order_and_wait_for_fill`

   Say:

   ```text
   Instead of handing beginners raw JSON, the wrapper gives them an OrderEvent with the fields they care about.
   ```

6. Run authenticated order-event watching.

   Requirements:

   - `COINBASE_API_KEY` and `COINBASE_API_SECRET` sourced
   - API key has `view`

   Safer demo:

   - Run the script.
   - During the `watch_order_events` window, manually place/cancel a far-away limit order in Coinbase Advanced.

7. Show the headline automation call.

   With `RUN_REAL_TAKE_PROFIT_DEMO=False`, the script prints the exact call:

   ```python
   client.buy_then_limit_sell_on_fill(
       product_id="BTC-USDC",
       fiat_amount="10",
       sell_price_multiplier="1.05"
   )
   ```

   Say:

   ```text
   The useful part is not magic profit. The useful part is the fill-driven primitive: place an order, wait for Coinbase to push the actual fill, then use the real filled size and average fill price for the follow-up order.
   ```

8. Optional real take-profit demo.

   Requirements:

   - API key has `trade`
   - You are comfortable spending the tiny amount
   - You understand the sell limit order may remain open

   Edit:

   ```python
   RUN_REAL_TAKE_PROFIT_DEMO = True
   TAKE_PROFIT_FIAT_AMOUNT = "10"
   SELL_PRICE_MULTIPLIER = "1.05"
   ```

   Optional cleanup:

   ```python
   CANCEL_OPEN_ORDERS_AT_END = True
   ```

   Say:

   ```text
   This places real orders. The follow-up sell is a take-profit order, not guaranteed profit. Fees and price movement still matter.
   ```

9. Show tests.

   Run:

   ```bash
   .venv/bin/python -m unittest discover -s coinbase_advanced_trader/tests
   ```

   Say:

   ```text
   This is the part vibe coding cannot skip: if the wrapper changes behavior, tests need to prove the workflow still does what we think it does.
   ```

Should you show vibe coding here?

Yes, but keep it scoped. The best vibe-coding beat is in Video 2:

- Ask the coding agent to add or explain a wrapper-level workflow.
- Show it reading the official SDK behavior first.
- Show it adding tests.
- Show tests passing.

Good prompt to show on camera:

```text
Use the official Coinbase SDK as the reference. In Rhett's wrapper repo, add a beginner-friendly dry-run volatility-targeted trend planner using public daily candles. It should not place orders. Expose it on EnhancedRESTClient and add tests.
```

Avoid vibe-coding a live trading bot that places orders without reviewing it. That is a bad teaching moment.

## Video 3: Running A WebSocket Bot 24/7

Working title:

```text
Running a Coinbase WebSocket Trading Bot 24/7
```

Big idea:

```text
Scheduled REST jobs fit Lambda. Persistent WebSocket bots want always-on compute.
```

What to have open:

- `video_3.py`
- Terminal
- AWS Console EC2 page
- Optional AWS Lambda timeout docs
- Optional SSH terminal into the EC2 instance
- Coinbase Advanced `BTC-USDC`

Script switches / env vars:

```bash
export COINBASE_BOT_PRODUCTS="BTC-USDC"
export COINBASE_BOT_RUN_FOREVER=0
export COINBASE_BOT_WATCH_SECONDS=60
export COINBASE_BOT_ENABLE_TREND_PLAN=1
export COINBASE_BOT_QUOTE_BUDGET=100
export COINBASE_BOT_TARGET_VOL=0.08
```

For local filming, keep `COINBASE_BOT_RUN_FOREVER=0`. For EC2/systemd footage, set it to `1`.

Demo flow:

1. Start with the Lambda contrast.

   Say:

   ```text
   Lambda is great for scheduled REST jobs, like buy once a day. But AWS Lambda has a 15-minute max timeout, and a WebSocket bot is shaped like a long-running process.
   ```

2. Show the architecture.

   ```text
   Coinbase WebSocket -> Python process on EC2 -> logs order events -> systemd restarts it -> REST handles slower reference data and recovery
   ```

   Say:

   ```text
   The bot does not need to be fancy to be useful. The first production habit is staying alive, logging clearly, and failing loudly when credentials are missing.
   ```

3. Run locally first.

   ```bash
   set -a
   source .env.video
   set +a

   export COINBASE_BOT_RUN_FOREVER=0
   export COINBASE_BOT_ENABLE_TREND_PLAN=1
   .venv/bin/python video_3.py
   ```

   Expected output:

   - startup logs
   - trend plan log, if public candles are reachable
   - order-event watch logs
   - clean exit after the watch window

4. Explain the separation.

   Point at:

   - `log_trend_plan`
   - `log_order_event`
   - `run_bot`

   Say:

   ```text
   The slow strategy check is separate from live order handling. REST candles build a plan. WebSocket user events maintain live order state.
   ```

5. Show EC2, but keep it simple.

   You do not need a full cloud engineering tutorial. Show the shape:

   - Launch a small Linux EC2 instance.
   - SSH into it.
   - Install Python and create a venv.
   - Install the wrapper package.
   - Copy or create a bot script.
   - Add env vars.
   - Run it with systemd.

   Important note: `video_3.py` is gitignored local filming code. It will not appear when someone installs the package from pip. For the EC2 demo, either:

   - copy `video_3.py` to the instance with `scp`, or
   - create a small `bot.py` on the instance using the same `EnhancedRESTClient` calls.

6. Example EC2 commands.

   These are filming notes, not a polished one-click installer:

   ```bash
   ssh ubuntu@YOUR_EC2_IP
   sudo apt update
   sudo apt install -y python3-venv

   mkdir -p ~/coinbase-bot
   cd ~/coinbase-bot
   python3 -m venv .venv
   source .venv/bin/activate
   pip install coinbase-advancedtrade-python
   ```

   From your Mac, if copying the local filming script:

   ```bash
   scp video_3.py ubuntu@YOUR_EC2_IP:/home/ubuntu/coinbase-bot/video_3.py
   ```

7. Show systemd shape.

   Do not show real secrets in the service file. Use placeholders on camera.

   `video_3.py` can print the example:

   ```bash
   PRINT_SYSTEMD_EXAMPLE=1 .venv/bin/python video_3.py
   ```

   Say:

   ```text
   systemd is the automation here. If the process exits, it restarts it. If the server reboots, it starts it again.
   ```

8. What to automate in AWS.

   Show EC2 + systemd for this video.

   Do not use Lambda for the WebSocket listener. Lambda can still be mentioned as the right tool for scheduled REST jobs.

   Optional advanced mention:

   ```text
   If I wanted to make this more cloud-native later, I would move logs into CloudWatch and deploy with Docker, ECS, or a small managed container service. But the beginner mental model is one always-on Python process.
   ```

9. Trigger a live order event.

   Safer option:

   - Keep bot running.
   - Place/cancel a far-away limit order manually in Coinbase Advanced.
   - Watch the EC2/local logs print the event.

   Stronger option:

   - Use the real take-profit flow from Video 2 locally.
   - Let Video 3 focus on deployment and monitoring, not another live trade.

10. End with the production warning.

   Say:

   ```text
   This is the deployment skeleton, not a complete institutional bot. Production still needs position limits, alerting, reconciliation, stale-data checks, and a kill switch.
   ```

Should you show vibe coding here?

Only lightly. Video 3 is more about deployment shape than code generation. A useful short beat:

```text
Ask the agent to turn the local bot into a systemd-ready process with env vars, logging, and loud startup failures.
```

Do not ask the agent to invent a profitable strategy live.

## Suggested Series Arc

Video 1 viewer leaves thinking:

```text
I can connect to Coinbase WebSockets, parse messages, and watch public/private events.
```

Video 2 viewer leaves thinking:

```text
The wrapper adds value by turning low-level SDK pieces into practical workflows, especially dry-run strategy planning and fill-driven order automation.
```

Video 3 viewer leaves thinking:

```text
A WebSocket bot needs always-on compute, logs, restarts, env vars, and operational guardrails.
```

## Open Choices Before Filming

Decide these before the final takes:

- Will Video 1 include a real tiny market buy, or only manual place/cancel?
- Will Video 2 run the real `buy_then_limit_sell_on_fill` flow, or only show the printed call?
- Will Video 3 show actual EC2 setup live, or use pre-created EC2 and focus on the bot/process manager?
- Will you keep product IDs as `BTC-USDC`, or switch to `BTC-USD` for audience familiarity?
- Do you want the vibe-coding beat in Video 2 to show implementation, explanation, or test-driven cleanup?

My default recommendation:

- Video 1: public ticker live, authenticated user channel with manual place/cancel, no real market buy unless the first take is smooth.
- Video 2: show the dry-run trend planner and normalized order events; optionally run the real take-profit flow once.
- Video 3: use a pre-created EC2 instance and show systemd/logging/restart behavior, not a long AWS setup from scratch.

## Source Notes

- Coinbase Advanced Trade supports REST and WebSocket APIs for trading/order management and market data: https://docs.cdp.coinbase.com/advanced-trade/docs/rest-api-overview
- Coinbase documents public Advanced Trade endpoints separately from private endpoints: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/rest-api
- Coinbase endpoint permissions distinguish `view`, `trade`, `transfer`, and related capabilities: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/data-api/get-api-key-permissions
- Coinbase WebSocket overview and channels: https://coinbase-cloud.mintlify.app/coinbase-app/advanced-trade-apis/websocket/websocket-overview and https://coinbase-cloud.mintlify.app/coinbase-app/advanced-trade-apis/websocket/websocket-channels
- AWS Lambda timeout is configurable up to 900 seconds, which is 15 minutes: https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html
- EC2 is the better beginner AWS shape for a persistent WebSocket daemon: https://aws.amazon.com/documentation-overview/ec2/
