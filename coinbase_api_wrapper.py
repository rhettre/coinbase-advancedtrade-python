import http.client
import hmac
import hashlib
import json
import time
import base64
import uuid
from enum import Enum
from datetime import datetime
from config import API_KEY, API_SECRET


class Side(Enum):
    BUY = 1
    SELL = 0


class Method(Enum):
    POST = "POST"
    GET = "GET"


def load_api_credentials():
    return [API_KEY, API_SECRET]


creds = load_api_credentials()


def generate_client_order_id():
    return uuid.uuid4()


def coinbase_request(method, path, body='', params=None):
    if params:
        query_params = '&'.join([f'{k}={v}' for k, v in params.items()])
        path = f'{path}?{query_params}'

    with http.client.HTTPSConnection("api.coinbase.com") as conn:
        timestamp = str(int(time.time()))
        message = timestamp + method.value + path.split('?')[0] + str(body)
        signature = hmac.new(creds[1].encode(
            'utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

        headers = {
            "accept": "application/json",
            "CB-ACCESS-KEY": creds[0],
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp
        }

        conn.request(method.value, path, body, headers)
        res = conn.getresponse()
        data = res.read()

        if res.status == 401:
            print("Error: Unauthorized. Please check your API key and secret.")
            return None

        try:
            response_data = json.loads(data.decode("utf-8"))
            return response_data
        except json.JSONDecodeError:
            print("Error: Unable to decode JSON response. Raw response data:", data)
            return None


def listAccounts(limit=49, cursor=None):
    return coinbase_request(Method.GET, '/api/v3/brokerage/accounts', params={'limit': limit, 'cursor': cursor})


def getAccount(account_uuid):
    return coinbase_request(Method.GET, f'/api/v3/brokerage/accounts/{account_uuid}')


def createOrder(client_order_id, product_id, side, order_configuration):
    body = json.dumps({
        "client_order_id": client_order_id,
        "product_id": product_id,
        "side": side,
        "order_configuration": order_configuration
    })
    return coinbase_request(Method.POST, '/api/v3/brokerage/orders', body)


def cancelOrders(order_ids):
    body = json.dumps({"order_ids": order_ids})
    return coinbase_request(Method.POST, '/api/v3/brokerage/orders/batch_cancel', body)


def listOrders(**kwargs):
    return coinbase_request(Method.GET, '/api/v3/brokerage/orders/historical/batch', params=kwargs)


def listFills(**kwargs):
    return coinbase_request(Method.GET, '/api/v3/brokerage/orders/historical/fills', params=kwargs)


def getOrder(order_id):
    return coinbase_request(Method.GET, f'/api/v3/brokerage/orders/historical/{order_id}')


def listProducts(**kwargs):
    return coinbase_request(Method.GET, '/api/v3/brokerage/products', params=kwargs)


def getProduct(product_id):
    return coinbase_request(Method.GET, f'/api/v3/brokerage/products/{product_id}')


def getProductCandles(product_id, start, end, granularity):
    params = {
        'start': start,
        'end': end,
        'granularity': granularity
    }
    return coinbase_request(Method.GET, f'/api/v3/brokerage/products/{product_id}/candles', params=params)


def getMarketTrades(product_id, limit):
    return coinbase_request(Method.GET, f'/api/v3/brokerage/products/{product_id}/ticker', params={'limit': limit})


def getTransactionsSummary(start_date, end_date, user_native_currency='USD', product_type='SPOT'):
    params = {
        'start_date': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'end_date': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'user_native_currency': user_native_currency,
        'product_type': product_type
    }
    return coinbase_request(Method.GET, '/api/v3/brokerage/transaction_summary', params=params)
