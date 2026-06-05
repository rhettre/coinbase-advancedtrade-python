import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, List, Optional, Tuple

from alphasquared import AlphaSquared

from .enhanced_rest_client import EnhancedRESTClient
from coinbase_advanced_trader.constants import DEFAULT_CONFIG
from coinbase_advanced_trader.models import Order
from coinbase_advanced_trader.utils import ensure_dict

logger = logging.getLogger(__name__)


class AlphaSquaredActionSkip(Exception):
    """Internal marker for valid actions that cannot safely place an order."""


@dataclass
class AlphaSquaredActionResult:
    """Result for a single AlphaSquared strategy action."""

    action_id: Optional[str]
    status: str
    side: Optional[str] = None
    value: Optional[Decimal] = None
    order: Optional[Order] = None
    acknowledgement: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    raw_action: Optional[Dict[str, Any]] = None
    portfolio_uuid: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        order = None
        if self.order:
            order = {
                "id": self.order.id,
                "product_id": self.order.product_id,
                "side": self.order.side.value,
                "type": self.order.type.value,
                "size": str(self.order.size),
                "price": str(self.order.price) if self.order.price is not None else None,
                "client_order_id": self.order.client_order_id,
                "status": self.order.status,
            }

        return {
            "action_id": self.action_id,
            "status": self.status,
            "side": self.side,
            "value": str(self.value) if self.value is not None else None,
            "order": order,
            "acknowledgement": self.acknowledgement,
            "reason": self.reason,
            "raw_action": self.raw_action,
            "portfolio_uuid": self.portfolio_uuid,
        }


class AlphaSquaredTrader:
    def __init__(self, coinbase_client: EnhancedRESTClient, alphasquared_client: AlphaSquared):
        self.coinbase_client = coinbase_client
        self.alphasquared_client = alphasquared_client

    def execute_strategy(self, product_id: str, strategy_name: str):
        try:
            asset, base_currency = product_id.split('-')
            
            current_risk = self.alphasquared_client.get_current_risk(asset)
            logger.info(f"Current {asset} Risk: {current_risk}")
            
            action, value = self.alphasquared_client.get_strategy_value_for_risk(strategy_name, current_risk)
            logger.info(f"Strategy suggests: Action = {action.upper()}, Value = {value}")
            
            if value <= 0:
                logger.info("No action taken based on current risk and strategy.")
                return
            
            if action.lower() == 'buy':
                self._execute_buy(product_id, value)
            elif action.lower() == 'sell':
                self._execute_sell(product_id, asset, base_currency, value)
            else:
                logger.info(f"Unknown action: {action}. No trade executed.")
        
        except Exception as e:
            logger.error(f"Error in execute_strategy: {str(e)}")
            logger.exception("Full traceback:")

    def execute_pending_strategy_actions(
        self,
        product_id: str,
        *,
        strategy_name: Optional[str] = None,
        strategy_id: Optional[int] = None,
        portfolio_uuid: Optional[str] = None,
        max_actions: int = 10,
        per_page: int = 50,
        timeout: Optional[float] = None,
        buy_post_only: bool = DEFAULT_CONFIG['POST_ONLY_DEFAULT'],
        sell_post_only: bool = DEFAULT_CONFIG['POST_ONLY_DEFAULT'],
        sell_price_multiplier: str = "1.005",
    ) -> List[AlphaSquaredActionResult]:
        """
        Execute pending AlphaSquared strategy actions against Coinbase.

        AlphaSquared is treated as the source of strategy intent. This method
        fetches pending actions, places at most one Coinbase order per action,
        and marks the AlphaSquared action executed only after Coinbase accepts
        the order.
        """
        self._require_strategy_selector(strategy_name, strategy_id)

        actions_page = self.alphasquared_client.get_strategy_actions(
            strategy_name=strategy_name,
            strategy_id=strategy_id,
            page=1,
            per_page=per_page,
            executed=False,
            timeout=timeout,
        )
        if self._has_error(actions_page):
            return [
                AlphaSquaredActionResult(
                    action_id=None,
                    status="failed",
                    reason=actions_page.get("error"),
                    raw_action=actions_page,
                )
            ]

        actions = actions_page.get("actions", []) if isinstance(actions_page, dict) else []
        action_limit = max(0, int(max_actions))
        if action_limit == 0:
            return []

        results: List[AlphaSquaredActionResult] = []
        resolved_portfolio_uuid = portfolio_uuid

        for raw_action in actions[:action_limit]:
            normalized, skip_reason = self._normalize_action(raw_action)
            if normalized is None:
                results.append(
                    AlphaSquaredActionResult(
                        action_id=self._action_id(raw_action),
                        status="skipped",
                        reason=skip_reason,
                        raw_action=raw_action if isinstance(raw_action, dict) else None,
                        portfolio_uuid=resolved_portfolio_uuid,
                    )
                )
                continue

            if resolved_portfolio_uuid is None:
                resolved_portfolio_uuid = self._get_default_portfolio_uuid()

            notification_id = normalized["notification_id"]
            side = normalized["side"]
            value = normalized["value"]
            client_order_id = self._deterministic_client_order_id(
                product_id=product_id,
                side=side,
                notification_id=notification_id,
                strategy_name=strategy_name,
                strategy_id=strategy_id,
            )

            try:
                order = self._execute_action_order(
                    product_id=product_id,
                    side=side,
                    value=value,
                    portfolio_uuid=resolved_portfolio_uuid,
                    client_order_id=client_order_id,
                    buy_post_only=buy_post_only,
                    sell_post_only=sell_post_only,
                    sell_price_multiplier=sell_price_multiplier,
                )
            except AlphaSquaredActionSkip as error:
                results.append(
                    AlphaSquaredActionResult(
                        action_id=notification_id,
                        status="skipped",
                        side=side,
                        value=value,
                        reason=str(error),
                        raw_action=raw_action,
                        portfolio_uuid=resolved_portfolio_uuid,
                    )
                )
                continue
            except Exception as error:
                logger.error(f"Coinbase order failed for AlphaSquared action {notification_id}: {error}")
                results.append(
                    AlphaSquaredActionResult(
                        action_id=notification_id,
                        status="failed",
                        side=side,
                        value=value,
                        reason=str(error),
                        raw_action=raw_action,
                        portfolio_uuid=resolved_portfolio_uuid,
                    )
                )
                continue

            acknowledgement = self.alphasquared_client.update_strategy_action_status(
                notification_id=notification_id,
                executed=True,
                strategy_name=strategy_name,
                strategy_id=strategy_id,
                timeout=timeout,
            )
            if self._has_error(acknowledgement):
                results.append(
                    AlphaSquaredActionResult(
                        action_id=notification_id,
                        status="ack_failed",
                        side=side,
                        value=value,
                        order=order,
                        acknowledgement=acknowledgement,
                        reason=acknowledgement.get("error"),
                        raw_action=raw_action,
                        portfolio_uuid=resolved_portfolio_uuid,
                    )
                )
                continue

            results.append(
                AlphaSquaredActionResult(
                    action_id=notification_id,
                    status="executed",
                    side=side,
                    value=value,
                    order=order,
                    acknowledgement=acknowledgement,
                    raw_action=raw_action,
                    portfolio_uuid=resolved_portfolio_uuid,
                )
            )

        return results

    def _execute_buy(self, product_id: str, value: float):
        try:
            order = self.coinbase_client.fiat_limit_buy(product_id, str(value), price_multiplier="0.995")
            if isinstance(order, Order):
                logger.info(f"Buy limit order placed: ID={order.id}, Size={order.size}, Price={order.price}")
            else:
                logger.warning(f"Unexpected order response type: {type(order)}")
        except Exception as e:
            logger.error(f"Error placing buy order: {str(e)}")
            logger.exception("Full traceback:")

    def _execute_sell(self, product_id, asset, base_currency, value):
        balance = Decimal(self.coinbase_client.get_crypto_balance(asset))
        logger.info(f"Current {asset} balance: {balance}")
        
        product_details = self.coinbase_client.get_product(product_id)
        base_increment = Decimal(product_details['base_increment'])
        quote_increment = Decimal(product_details['quote_increment'])
        current_price = Decimal(product_details['price'])
        logger.info(f"Current {asset} price: {current_price} {base_currency}")

        sell_amount = (balance * Decimal(value) / Decimal('100')).quantize(base_increment, rounding=ROUND_DOWN)
        logger.info(f"Sell amount: {sell_amount} {asset}")

        if sell_amount > base_increment:
            limit_price = (current_price * Decimal('1.005')).quantize(quote_increment, rounding=ROUND_DOWN)
            
            order = self.coinbase_client.limit_order_gtc_sell(
                client_order_id=self.coinbase_client._order_service._generate_client_order_id(),
                product_id=product_id,
                base_size=str(sell_amount),
                limit_price=str(limit_price)
            )
            
            logger.info(f"Sell limit order placed for {sell_amount} {asset} at {limit_price} {base_currency}: {order}")
        else:
            logger.info(f"Sell amount {sell_amount} {asset} is too small. Minimum allowed is {base_increment}. No order placed.")

    @staticmethod
    def _require_strategy_selector(
        strategy_name: Optional[str],
        strategy_id: Optional[int]
    ) -> None:
        if bool(strategy_name) ^ bool(strategy_id):
            return
        raise ValueError("Provide exactly one of strategy_name or strategy_id.")

    @staticmethod
    def _has_error(result: Any) -> bool:
        return isinstance(result, dict) and "error" in result

    @staticmethod
    def _action_id(action: Any) -> Optional[str]:
        if not isinstance(action, dict):
            return None
        value = AlphaSquaredTrader._first_present(
            action,
            "notificationId",
            "notification_id",
            "id",
        )
        return str(value) if value is not None else None

    @staticmethod
    def _first_present(action: Dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = action.get(key)
            if value not in (None, ""):
                return value
        return None

    def _normalize_action(
        self,
        action: Any
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        if not isinstance(action, dict):
            return None, "AlphaSquared action is not a dictionary."

        notification_id = self._first_present(
            action,
            "notificationId",
            "notification_id",
            "id",
        )
        if notification_id is None:
            return None, "AlphaSquared action is missing notificationId."

        side = self._normalize_side(
            self._first_present(
                action,
                "type",
                "action",
                "side",
                "actionType",
                "action_type",
            )
        )
        if side is None:
            return None, "AlphaSquared action type is not BUY or SELL."

        raw_value = self._first_present(
            action,
            "value",
            "amount",
            "strategyValue",
            "strategy_value",
        )
        if raw_value is None:
            return None, "AlphaSquared action is missing a value or amount."

        try:
            value = Decimal(str(raw_value))
        except Exception:
            return None, f"AlphaSquared action value is not numeric: {raw_value}"

        if value <= 0:
            return None, "AlphaSquared action value must be greater than zero."

        return {
            "notification_id": str(notification_id),
            "side": side,
            "value": value,
        }, ""

    @staticmethod
    def _normalize_side(raw_side: Any) -> Optional[str]:
        if raw_side is None:
            return None
        side_text = str(raw_side).strip().lower().replace("_", " ").replace("-", " ")
        if "buy" in side_text:
            return "buy"
        if "sell" in side_text:
            return "sell"
        return None

    @staticmethod
    def _deterministic_client_order_id(
        *,
        product_id: str,
        side: str,
        notification_id: str,
        strategy_name: Optional[str],
        strategy_id: Optional[int],
    ) -> str:
        strategy_key = strategy_name or str(strategy_id)
        seed = f"alphasquared:{strategy_key}:{notification_id}:{product_id}:{side}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))

    def _get_default_portfolio_uuid(self) -> str:
        response = self.coinbase_client.get_portfolios("DEFAULT")
        response_dict = ensure_dict(response)
        portfolios = response_dict.get("portfolios") or []
        for portfolio in portfolios:
            portfolio_dict = ensure_dict(portfolio)
            portfolio_uuid = portfolio_dict.get("uuid")
            if portfolio_uuid:
                return str(portfolio_uuid)
        raise ValueError("Could not resolve Coinbase default portfolio UUID.")

    def _execute_action_order(
        self,
        *,
        product_id: str,
        side: str,
        value: Decimal,
        portfolio_uuid: str,
        client_order_id: str,
        buy_post_only: bool,
        sell_post_only: bool,
        sell_price_multiplier: str,
    ) -> Order:
        if side == "buy":
            return self.coinbase_client.fiat_limit_buy(
                product_id,
                str(value),
                post_only=buy_post_only,
                client_order_id=client_order_id,
                retail_portfolio_id=portfolio_uuid,
            )
        if side == "sell":
            return self._execute_action_sell(
                product_id=product_id,
                percent_to_sell=value,
                portfolio_uuid=portfolio_uuid,
                client_order_id=client_order_id,
                post_only=sell_post_only,
                sell_price_multiplier=sell_price_multiplier,
            )
        raise AlphaSquaredActionSkip(f"Unsupported AlphaSquared action side: {side}")

    def _execute_action_sell(
        self,
        *,
        product_id: str,
        percent_to_sell: Decimal,
        portfolio_uuid: str,
        client_order_id: str,
        post_only: bool,
        sell_price_multiplier: str,
    ) -> Order:
        asset, quote_currency = product_id.split('-')
        balance = Decimal(
            self.coinbase_client.get_crypto_balance(
                asset,
                retail_portfolio_id=portfolio_uuid,
            )
        )
        logger.info(f"Current {asset} balance in portfolio {portfolio_uuid}: {balance}")

        product_details = ensure_dict(self.coinbase_client.get_product(product_id))
        base_increment = Decimal(str(product_details['base_increment']))
        quote_increment = Decimal(str(product_details['quote_increment']))
        current_price = Decimal(str(product_details['price']))
        logger.info(f"Current {asset} price: {current_price} {quote_currency}")

        sell_amount = (
            balance * percent_to_sell / Decimal('100')
        ).quantize(base_increment, rounding=ROUND_DOWN)
        if sell_amount <= base_increment:
            raise AlphaSquaredActionSkip(
                f"Sell amount {sell_amount} {asset} is too small. Minimum allowed is {base_increment}."
            )

        limit_price = (
            current_price * Decimal(str(sell_price_multiplier))
        ).quantize(quote_increment, rounding=ROUND_DOWN)

        return self.coinbase_client.limit_sell_base_size(
            product_id=product_id,
            base_size=str(sell_amount),
            limit_price=str(limit_price),
            post_only=post_only,
            client_order_id=client_order_id,
            retail_portfolio_id=portfolio_uuid,
        )
