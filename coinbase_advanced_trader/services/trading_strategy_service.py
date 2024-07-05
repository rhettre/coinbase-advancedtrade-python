from abc import ABC, abstractmethod
from coinbase_advanced_trader.models import Order
from .order_service import OrderService
from .price_service import PriceService

class BaseTradingStrategy(ABC):
    def __init__(self, order_service: OrderService, price_service: PriceService):
        self.order_service = order_service
        self.price_service = price_service

    @abstractmethod
    def execute_trade(self, product_id: str, fiat_amount: str) -> Order:
        pass
