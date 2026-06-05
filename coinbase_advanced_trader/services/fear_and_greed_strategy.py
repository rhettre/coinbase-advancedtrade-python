import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fear_and_greed import FearAndGreedIndex

from coinbase_advanced_trader.config import config_manager
from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.models import Order
from .trading_strategy_service import BaseTradingStrategy


DEFAULT_STATIC_FGI_LADDER: List[Dict[str, Any]] = [
    {"name": "extreme_fear", "max": 24, "action": "buy", "amount": "2.00"},
    {"name": "fear", "min": 25, "max": 44, "action": "buy", "amount": "1.25"},
    {"name": "neutral", "min": 45, "max": 74, "action": "hold", "amount": "0"},
    {"name": "greed", "min": 75, "action": "sell", "amount": "1.00"},
]


class FearAndGreedStrategy(BaseTradingStrategy):
    """
    A trading strategy based on the Fear and Greed Index (FGI).
    """

    def __init__(self, order_service, price_service, config, account_service=None):
        """
        Initialize the FearAndGreedStrategy.

        :param order_service: Service for handling orders.
        :param price_service: Service for handling prices.
        :param config: Configuration object.
        """
        super().__init__(order_service, price_service)
        self.config = config
        self.account_service = account_service
        self._fgi_client = FearAndGreedIndex()

    def execute_trade(self, product_id: str, fiat_amount: str) -> Optional[Order]:
        """
        Execute a trade based on the Fear and Greed Index (FGI).

        :param product_id: The product identifier for the trade.
        :param fiat_amount: The amount of fiat currency to trade.
        :return: An Order object if a trade is executed, None otherwise.
        """
        fgi = self._fgi_client.get_current_value()
        fgi_classification = self._fgi_client.get_current_classification()
        
        logger.info(f"FGI retrieved: {fgi} ({fgi_classification}) "
                    f"for trading {product_id}")

        fiat_amount = Decimal(fiat_amount)
        schedule = self.config.get_fgi_schedule()

        for condition in schedule:
            if self._should_execute_trade(condition, fgi):
                adjusted_amount = fiat_amount * Decimal(condition['factor'])
                logger.info(f"FGI condition met: FGI {fgi} "
                            f"{condition['action']} condition. "
                            f"Executing {condition['action']} with "
                            f"adjusted amount {adjusted_amount:.2f}")
                return self._execute_trade(product_id, str(adjusted_amount),
                                           condition['action'])

        logger.warning(f"No trading condition met for FGI: {fgi}")
        return None

    def _execute_trade(self, product_id: str, fiat_amount: str,
                       action: str) -> Optional[Order]:
        """
        Execute a buy or sell trade based on the given action.

        :param product_id: The product identifier for the trade.
        :param fiat_amount: The amount of fiat currency to trade.
        :param action: The trade action ('buy' or 'sell').
        :return: An Order object if the trade is executed successfully,
                 None otherwise.
        """
        if action == 'buy':
            return self.order_service.fiat_limit_buy(product_id, fiat_amount)
        elif action == 'sell':
            return self.order_service.fiat_limit_sell(product_id, fiat_amount)
        else:
            logger.error(f"Invalid action: {action}")
            return None

    def execute_static_ladder(
        self,
        product_id: str,
        portfolio_uuid: str,
        base_amount: str = "1.00",
        ladder: Optional[List[Dict[str, Any]]] = None,
        trade_date: Optional[str] = None,
        job_name: str = "fear_and_greed",
        post_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a static-dollar Fear & Greed ladder against one Coinbase portfolio.

        The ladder chooses a static quote-currency amount to buy or sell. It does
        not use percentage-of-portfolio sizing.
        """
        if not portfolio_uuid:
            raise ValueError("portfolio_uuid is required for static FGI ladder trades.")

        fgi = int(self._fgi_client.get_current_value())
        fgi_classification = self._fgi_client.get_current_classification()
        rule = self._match_static_ladder_rule(
            fgi,
            ladder or DEFAULT_STATIC_FGI_LADDER
        )

        if not rule or str(rule.get("action", "hold")).lower() == "hold":
            return self._static_ladder_result(
                job_name=job_name,
                status="skipped",
                product_id=product_id,
                portfolio_uuid=portfolio_uuid,
                fgi=fgi,
                fgi_classification=fgi_classification,
                rule=rule,
                reason="No static ladder trade for current Fear & Greed value.",
            )

        action = str(rule["action"]).lower()
        quote_amount = self._static_ladder_amount(rule, Decimal(str(base_amount)))
        if quote_amount <= 0:
            return self._static_ladder_result(
                job_name=job_name,
                status="skipped",
                product_id=product_id,
                portfolio_uuid=portfolio_uuid,
                fgi=fgi,
                fgi_classification=fgi_classification,
                rule=rule,
                reason="Static ladder amount must be greater than zero.",
            )

        trade_date = trade_date or datetime.now(timezone.utc).date().isoformat()
        client_order_id = self._static_ladder_client_order_id(
            job_name=job_name,
            trade_date=trade_date,
            product_id=product_id,
            portfolio_uuid=portfolio_uuid,
            action=action,
            rule_name=str(rule.get("name", "rule")),
        )

        if action == "buy":
            order = self.order_service.fiat_limit_buy(
                product_id,
                str(quote_amount),
                post_only=post_only,
                client_order_id=client_order_id,
                retail_portfolio_id=portfolio_uuid,
            )
        elif action == "sell":
            skip_reason = self._static_sell_skip_reason(product_id, portfolio_uuid)
            if skip_reason:
                return self._static_ladder_result(
                    job_name=job_name,
                    status="skipped",
                    product_id=product_id,
                    portfolio_uuid=portfolio_uuid,
                    fgi=fgi,
                    fgi_classification=fgi_classification,
                    rule=rule,
                    action=action,
                    quote_amount=quote_amount,
                    reason=skip_reason,
                )
            order = self.order_service.fiat_limit_sell(
                product_id,
                str(quote_amount),
                post_only=post_only,
                client_order_id=client_order_id,
                retail_portfolio_id=portfolio_uuid,
            )
        else:
            return self._static_ladder_result(
                job_name=job_name,
                status="skipped",
                product_id=product_id,
                portfolio_uuid=portfolio_uuid,
                fgi=fgi,
                fgi_classification=fgi_classification,
                rule=rule,
                action=action,
                quote_amount=quote_amount,
                reason=f"Unsupported static ladder action: {action}",
            )

        return self._static_ladder_result(
            job_name=job_name,
            status="executed",
            product_id=product_id,
            portfolio_uuid=portfolio_uuid,
            fgi=fgi,
            fgi_classification=fgi_classification,
            rule=rule,
            action=action,
            quote_amount=quote_amount,
            order=order,
        )

    @staticmethod
    def _should_execute_trade(condition: dict, fgi: int) -> bool:
        """
        Determine if a trade should be executed based on the condition and FGI.

        :param condition: The trading condition.
        :param fgi: The current Fear and Greed Index value.
        :return: True if the trade should be executed, False otherwise.
        """
        return ((condition['action'] == 'buy' and fgi <= condition['threshold'])
                or (condition['action'] == 'sell' and
                    fgi >= condition['threshold']))

    @staticmethod
    def _match_static_ladder_rule(
        fgi: int,
        ladder: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        for rule in ladder:
            min_value = rule.get("min")
            max_value = rule.get("max")
            if min_value is not None and fgi < int(min_value):
                continue
            if max_value is not None and fgi > int(max_value):
                continue
            return rule
        return None

    @staticmethod
    def _static_ladder_amount(rule: Dict[str, Any], base_amount: Decimal) -> Decimal:
        if "amount" in rule:
            return Decimal(str(rule["amount"]))
        return base_amount * Decimal(str(rule.get("factor", "1")))

    @staticmethod
    def _static_ladder_client_order_id(
        *,
        job_name: str,
        trade_date: str,
        product_id: str,
        portfolio_uuid: str,
        action: str,
        rule_name: str,
    ) -> str:
        seed = f"fgi-static:{job_name}:{trade_date}:{product_id}:{portfolio_uuid}:{action}:{rule_name}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))

    def _static_sell_skip_reason(
        self,
        product_id: str,
        portfolio_uuid: str
    ) -> Optional[str]:
        if not self.account_service:
            return None
        asset = product_id.split("-")[0]
        balance = self.account_service.get_crypto_balance(
            asset,
            retail_portfolio_id=portfolio_uuid,
        )
        if balance <= 0:
            return f"No {asset} balance available to sell."
        return None

    @staticmethod
    def _static_ladder_result(
        *,
        job_name: str,
        status: str,
        product_id: str,
        portfolio_uuid: str,
        fgi: int,
        fgi_classification: str,
        rule: Optional[Dict[str, Any]],
        action: Optional[str] = None,
        quote_amount: Optional[Decimal] = None,
        order: Optional[Order] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        order_dict = None
        if order:
            order_dict = {
                "id": order.id,
                "product_id": order.product_id,
                "side": order.side.value,
                "type": order.type.value,
                "size": str(order.size),
                "price": str(order.price) if order.price is not None else None,
                "client_order_id": order.client_order_id,
                "status": order.status,
            }
        return {
            "job": job_name,
            "kind": "fear_and_greed",
            "status": status,
            "product_id": product_id,
            "portfolio_uuid": portfolio_uuid,
            "fgi_value": fgi,
            "fgi_classification": fgi_classification,
            "rule": rule,
            "action": action,
            "quote_amount": str(quote_amount) if quote_amount is not None else None,
            "order": order_dict,
            "reason": reason,
        }
