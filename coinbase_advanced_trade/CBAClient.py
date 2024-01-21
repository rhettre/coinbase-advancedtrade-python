import http.client
import hmac
import hashlib
import json
import time
from enum import Enum
from urllib.parse import urlencode
from typing import Any, Dict, Union, Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from dotenv import load_dotenv
import os
from coinbase_advanced_trade.product import Product
from coinbase_advanced_trade.account import Account
import logging
from decimal import Decimal, ROUND_HALF_UP
class Side(Enum):
    BUY = 1
    SELL = 0


class Method(Enum):
    POST = "POST"
    GET = "GET"


def setup_logging_to_file(filepath: str, level: int = logging.INFO) -> None:
    """
    Set up logging to a specified file.

    :param filepath: The path to the log file.
    :param level: The logging level (e.g., logging.INFO, logging.DEBUG).
    """
    try:
        # Create a logger
        logger = logging.getLogger()
        logger.setLevel(level)

        # Create a file handler that logs to the specified filepath
        file_handler = logging.FileHandler(filepath)

        # Create a formatter and set it for the file handler
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)

    except Exception as e:
        print(f"Error setting up logging: {e}")


class CBAClient:
    cached_products:dict[str,Any] = {'timestamp':0,'products':{}} 
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        log_path: str = "CBAClient.log",
        simulate: bool = False,
    ) -> None:
        self.simulate: bool = simulate
        setup_logging_to_file(log_path)
        self.log_path: str = log_path

        if api_key and api_secret:
            self.key: str = api_key
            self.secret: str = api_secret
        else:
            self.key = os.getenv("COINBASE_API_KEY", "")
            self.secret = os.getenv("COINBASE_API_SECRET", "")
            if not self.key or not self.secret:
                load_dotenv()
                self.key = os.getenv("COINBASE_API_KEY", "")
                self.secret = os.getenv("COINBASE_API_SECRET", "")
            if not self.key or not self.secret:
                raise Exception("Error: API keys not found. Please set the environment variables COINBASE_API_KEY and COINBASE_API_SECRET\n\
or by creating a file named .env in the root directory of your project and adding your keys to it.\n\
or by simply passing them to this funciton, note this is much less secure.\n"
                )

    def __call__(
        self,
        method: str,
        path: str,
        body: Union[Dict[str, Any], str] = "",
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[Any, Any]:
        path = self.add_query_params(path, params)
        body_encoded: bytes = self.prepare_body(body)
        headers: Dict[str, str] = self.create_headers(method, path, body)
        return self.send_request(method, path, body_encoded, headers)

    def add_query_params(self, path: str, params: Optional[Dict[str, str]]) -> str:
        if params:
            query_params: str = urlencode(params)
            path = f"{path}?{query_params}"
        return path

    def prepare_body(self, body: Union[Dict[str, Any], str]) -> bytes:
        return json.dumps(body).encode("utf-8") if body else b""

    def create_headers(
        self, method: str, path: str, body: Union[Dict[str, Any], str]
    ) -> Dict[str, str]:
        timestamp = str(int(time.time()))
        message = (
            timestamp
            + method.upper()
            + path.split("?")[0]
            + (json.dumps(body) if body else "")
        )
        signature = hmac.new(
            self.secret.encode("utf-8"),
            message.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        return {
            "Content-Type": "application/json",
            "CB-ACCESS-KEY": self.key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
        }

    def send_request(
        self, method: str, path: str, body_encoded: bytes, headers: Dict[str, str]
    ) -> Dict[Any, Any]:
        conn = http.client.HTTPSConnection("api.coinbase.com")
        data = None
        try:
            conn.request(method, path, body_encoded, headers)
            res = conn.getresponse()
            data = res.read()
            if res.status == 401:
                raise Exception(
                    "Error: Unauthorized. Please check your API key and secret."
                )

            response_data = json.loads(data.decode("utf-8"))
            if "error_details" in response_data:
                if response_data["error_details"] == "missing required scopes":
                    raise Exception(
                        "Error: Missing Required Scopes. Please update your API Keys to include more permissions."
                    )
                else:
                    raise Exception(
                        f"Error from api request: {response_data}. "
                    )

            return response_data
        except json.JSONDecodeError:
            raise Exception(
                "Error: Unable to decode JSON response. Raw response data:", data
            )
        finally:
            conn.close()

    def generate_client_order_id(self) -> str:
        return str(uuid4())

    def listAccounts(self, limit: int = 250, cursor: str = "") -> list[Account]:
        products: dict[str, Product] = self.getProductsDict()
        raw_accounts_response: dict[str, Any] = self(
            Method.GET.value,
            "/api/v3/brokerage/accounts",
            params={"limit": limit, "cursor": cursor},#type: ignore 
        )

        raw_accounts: list[dict[str, Any]] = raw_accounts_response["accounts"]

        logging.info(f"Found {len(raw_accounts)} accounts")
        for i in range(len(raw_accounts)):
            currency = raw_accounts[i]["currency"]
            if currency == "USD":
                raw_accounts[i]["current_value"] = float(
                    raw_accounts[i]["available_balance"]["value"]
                )
            elif f"{currency}-USD" in products.keys():
                raw_accounts[i]["current_value"] = (
                    float(raw_accounts[i]["available_balance"]["value"])
                    * products[f"{currency}-USD"].price
                )
            else:
                raw_accounts[i]["current_value"] = 0

        accounts: list[Account] = [
            Account(raw_account)
            for raw_account in raw_accounts
            if raw_account["current_value"] > 0
        ]
        if raw_accounts_response["has_next"]:
            accounts.extend(self.listAccounts(limit, raw_accounts_response["cursor"]))

        return accounts

    def getAccountsDict(self, limit: int = 250, cursor: str = "") -> Dict[str, Account]:
        accounts: list[Account] = self.listAccounts(limit, cursor)
        accounts_dict: dict[str, Account] = {}
        for account in accounts:
            accounts_dict[account.currency] = account
        return accounts_dict

    def getAccountByCurrency(self, currency: str) -> Account:
        accounts: dict[str, Account] = self.getAccountsDict()
        return accounts[currency]

    def getAccount(self, account_uuid: Union[str, UUID]) -> Account:
        if isinstance(account_uuid, UUID):
            account_uuid = str(account_uuid)
        raw_account: dict[str, Any] = self(
            Method.GET.value, f"/api/v3/brokerage/accounts/{account_uuid}"
        )
        currency: str = raw_account["currency"]
        products: dict[str, Product] = self.getProductsDict()
        if currency == "USD":
            raw_account["current_value"] = float(
                raw_account["available_balance"]["value"]
            )
        elif f"{currency}-USD" in products.keys():
            raw_account["current_value"] = (
                float(raw_account["available_balance"]["value"])
                * products[f"{currency}-USD"].price
            )
        else:
            raw_account["current_value"] = 0
        account: Account = Account(raw_account)
        return account

    def createOrder(
        self,
        client_order_id: Union[str, UUID],
        product_id: str,
        side: Side,
        order_configuration: Dict[str, Any],
    ) -> Dict[Any, Any]:
        payload: Dict[str, Union[str, UUID, Side, Dict[str, Any]]] = {
            "client_order_id": str(client_order_id),
            "product_id": product_id,
            "side": side.value,#type: ignore
            "order_configuration": order_configuration,
        }
        if self.simulate:
            logging.info(f"Simulating order creation: {payload}")
            return {}

        created_order = self(Method.POST.value, "/api/v3/brokerage/orders", payload)
        return created_order

    def cancelOrders(self, order_ids: List[Union[str, UUID]]) -> Dict[Any, Any]:
        order_ids = [
            str(order_id) if isinstance(order_id, UUID) else order_id
            for order_id in order_ids
        ]
        body = {"order_ids": order_ids}
        canceled_orders = self(
            Method.POST.value, "/api/v3/brokerage/orders/batch_cancel", body
        )
        return canceled_orders

    def listOrders(self, **kwargs: Optional[dict[str, Any]]) -> Dict[Any, Any]:
        return self(
            Method.GET.value, "/api/v3/brokerage/orders/historical/batch", params=kwargs
        )

    def listFills(self, **kwargs: Optional[dict[str, Any]]) -> Dict[Any, Any]:
        return self(
            Method.GET.value, "/api/v3/brokerage/orders/historical/fills", params=kwargs
        )

    def getOrder(self, order_id: Union[str, UUID]) -> Dict[Any, Any]:
        order_id = str(order_id) if isinstance(order_id, UUID) else order_id
        return self(Method.GET.value, f"/api/v3/brokerage/orders/historical/{order_id}")

    def listProducts(self, max_age_seconds:float = 60,**kwargs: Optional[dict[str, Any]]) -> list[Product]:
        if time.time() - self.cached_products['timestamp'] < max_age_seconds:
            logging.info(f"Using cached products, this cache is {time.time() - self.cached_products['timestamp']} seconds old")
            #this helps keep from calling the api too much so you dont get rate limited.
            return self.cached_products['products']
        raw_products = self(
            Method.GET.value, "/api/v3/brokerage/products", params=kwargs
        )["products"]
        raw_products = [
            raw_product
            for raw_product in raw_products
            if raw_product["status"] == "online"
        ]
        products: list[Product] = [Product(raw_product) for raw_product in raw_products]
        logging.info(f"Found {len(products)} products")
        self.cached_products['timestamp'] = time.time()
        self.cached_products['products'] = products
        return products

    def getProductsDict(self, **kwargs: Optional[dict[str, Any]]) -> Dict[str, Product]:
        products: list[Product] = self.listProducts(**kwargs)  # type: ignore kwargs
        prodcuts_dict: dict[str, Product] = {}
        for product in products:
            prodcuts_dict[product.product_id] = product
        return prodcuts_dict

    def getProduct(self, product_id: str) -> Product:
        raw_product: Dict[str, Any] = self(
            Method.GET.value, f"/api/v3/brokerage/products/{product_id}"
        )
        return Product(raw_product)

    def getProductCandles(
        self, product_id: str, start: datetime, end: datetime, granularity: int
    ) -> Dict[Any, Any]:
        params = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "granularity": granularity,
        }
        return self(
            Method.GET.value,
            f"/api/v3/brokerage/products/{product_id}/candles",
            params=params,
        )

    def getMarketTrades(self, product_id: str, limit: int) -> Dict[Any, Any]:
        return self(
            Method.GET.value,
            f"/api/v3/brokerage/products/{product_id}/ticker",
            params={"limit": limit},
        )

    def getTransactionsSummary(
        self,
        start_date: datetime,
        end_date: datetime,
        user_native_currency: str = "USD",
        product_type: str = "SPOT",
        contract_expiry_type: str = "UNKNOWN_CONTRACT_EXPIRY_TYPE",
    ) -> Dict[Any, Any]:
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "user_native_currency": user_native_currency,
            "product_type": product_type,
            "contract_expiry_type": contract_expiry_type,
        }
        return self(Method.GET.value, "/api/v3/brokerage/transaction_summary", params)

    def get_spot_price(self, product_id: str) -> Optional[float]:
        """
        Fetches the current spot price of a specified product.

        Args:
            product_id (str): The ID of the product (e.g., "BTC-USD").

        Returns:
            float: The spot price as a float, or None if an error occurs.
        """
        
        product: Product = self.getProduct(product_id)
        return product.price
            
    def get_current_funds(self) -> float:
        """
        Calculates the total available cash balance across all cash accounts.

        Returns:
            float: The total available cash balance.
        """
        try:
            total_cash = 0.0
            accounts: list[Account] = self.listAccounts()
            for account in accounts:
                # Assuming the cash accounts are identified by 'USD' or similar currency codes
                if account.currency == "USD":
                    available_balance = float(account.available_balance["value"])
                    total_cash += available_balance
            return total_cash
        except Exception as e:
            logging.error(f"Error fetching current cash funds: {e}")
            return 0.0

    def fiat_limit_buy(self, product: Product, fiat_amount: float, price: float) -> Dict[Any, Any]:
        try:
            maker_fee_rate = Decimal("0.004")

            # Round the quote_increment to a reasonable number of decimal places
            quote_increment = Decimal(product.quote_increment).quantize(Decimal('0.00000000000000001'), rounding=ROUND_HALF_UP).normalize()


            raw_price = Decimal(price)
            limit_price: Decimal = raw_price.quantize(quote_increment)

            effective_fiat_amount: Decimal = Decimal(fiat_amount) * (1 - maker_fee_rate)
            raw_size: Decimal = (effective_fiat_amount / limit_price) / Decimal(product.base_increment)
            base_size: Decimal = (
                raw_size.quantize(Decimal("1.0"), rounding=ROUND_HALF_UP) * Decimal(product.base_increment)
            )
            if base_size < Decimal(product.base_min_size):
                raise ValueError(
                    f"Error: The calculated base size ({base_size}) is less than the minimum base size ({product.base_min_size})"
                )
            if base_size > Decimal(product.base_max_size):
                raise ValueError(
                    f"Error: The calculated base size ({base_size}) is greater than the maximum base size ({product.base_max_size})"
                )
            order_configuration: dict[str,dict[str, str | bool]] = {"limit_limit_gtc": {
                "limit_price": str(limit_price),
                "base_size": str(base_size),
                "post_only": True,
            }}

            order_details = self.createOrder(
                client_order_id=self.generate_client_order_id(),
                product_id=product.product_id,
                side=Side.BUY,
                order_configuration=order_configuration,
            )

            return order_details

        except Exception as e:
            logging.error(f"Error creating limit buy: {e}")
            raise ValueError(f"could not create limit buy got error: {e}")

    def fiat_limit_sell(
        self, product: Product, fiat_amount: float, price: float
    ) -> Dict[str, Any]:
        """
        Places a limit sell order.

        Args:
            product_id (str): The ID of the product to sell (e.g., "BTC-USD").
            fiat_amount (float): The amount in fiat to receive from selling.
            price_multiplier (float, optional): Multiplier to apply to the current spot price to get the limit price.

        Returns:
            dict: The response of the order details.
        """
        maker_fee_rate = Decimal("0.004")
        quote_increment: Decimal = Decimal(product.quote_increment).quantize(Decimal('0.00000000000000001'), rounding=ROUND_HALF_UP).normalize()
        base_increment = Decimal(product.base_increment).quantize(Decimal('0.00000000000000001'), rounding=ROUND_HALF_UP).normalize()
        limit_price = Decimal(price)
        limit_price: Decimal = limit_price.quantize(quote_increment)
        effective_fiat_amount: Decimal = Decimal(fiat_amount) / (1 - maker_fee_rate)
        raw_size: Decimal = (effective_fiat_amount / limit_price) 
        base_size: Decimal = (
            raw_size.quantize(Decimal(base_increment), rounding=ROUND_HALF_UP) 
        ).normalize()

        if base_size < Decimal(product.base_min_size):
            raise ValueError(
                f"Error: The calculated base size ({base_size}) is less than the minimum base size ({product.base_min_size})"
            )
        if base_size > Decimal(product.base_max_size):
            raise ValueError(
                f"Error: The calculated base size ({base_size}) is greater than the maximum base size ({product.base_max_size})"
            )

        order_configuration: dict[str,dict[str, str | bool]] = {"limit_limit_gtc":{
            "limit_price": str(limit_price),
            "base_size": str(base_size),
            "post_only": True,
        }}

        order_details:dict[str,Any] = self.createOrder(
            client_order_id=self.generate_client_order_id(),
            product_id=product.product_id,
            side=Side.SELL,
            order_configuration=order_configuration,
        )

        return order_details

    def buy(
        self,
        product: Product,
        fiat_amount: Optional[float] = None,
        price: Optional[float] = None,
        quantity: Optional[float] = None, #type: ignore
        percentage_of_funds: Optional[float] = None,
        current_price_ratio: float = 1.0005,# by default limit buy for 0.05% more than current price
    ) -> Dict[str, Any]:
        if not price:
            price = product.price * current_price_ratio
        if not fiat_amount:
            if percentage_of_funds:
                fiat_amount = percentage_of_funds * self.get_current_funds()
            else:
                if quantity and price:
                    fiat_amount = quantity * price
                else:
                    raise Exception(
                        "Error: Must specify either fiat_amount or quantity or percentage_of_funds"
                    )
        if not quantity and fiat_amount and price:
            quantity: float = fiat_amount / price
        
        logging.info(f"Buying {quantity} {product.base_currency_id} for {fiat_amount} {product.quote_currency_id} at {price} {product.quote_currency_id} per {product.base_currency_id}")
        if fiat_amount and price:
            result = self.fiat_limit_buy(product, fiat_amount, price)
        else:
            raise Exception(
                "Error: could not find fiat_amount and price"
            )
        return result

    def sell(
        self,
        product: Product,
        fiat_amount: Optional[float] = None,
        price: Optional[float] = None,
        quantity: Optional[float] = None, #type: ignore
        percentage_of_currency: Optional[float] = None,
        current_price_ratio: float = 0.9995, # by default limit sell for 0.05% less than current price
    ) -> Dict[str, Any]:
        if not price:
            price = product.price * current_price_ratio
        if not fiat_amount:
            if percentage_of_currency and not quantity:
                account: Account = self.getAccountByCurrency(product.base_currency_id)
                fiat_amount = percentage_of_currency * account.current_value
            elif quantity and price:
                fiat_amount = quantity * price
            else:
                raise Exception(
                    "Error: Must specify either fiat_amount or quantity or percentage_of_currency"
                )
        if not quantity and fiat_amount and price:
            quantity: float = fiat_amount / price
        elif not quantity and percentage_of_currency:
            account: Account = self.getAccountByCurrency(product.base_currency_id)
            quantity: float = percentage_of_currency * float(account.available_balance["value"])
        logging.info(f"Selling {quantity} {product.base_currency_id} for {fiat_amount} {product.quote_currency_id} at {price} {product.quote_currency_id} per {product.base_currency_id}")
        if fiat_amount and price:
            result = self.fiat_limit_sell(product, fiat_amount, price)
        else:
            raise Exception(
                "Error: could not find fiat_amount and price"
            )
        return result
