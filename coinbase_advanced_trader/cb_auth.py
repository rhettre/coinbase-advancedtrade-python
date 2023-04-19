import http.client
import hmac
import hashlib
import json
import time
from typing import Dict
from coinbase_advanced_trader.config import API_KEY, API_SECRET


class CBAuth:
    def __init__(self, api_key, api_secret):
        self.key = api_key
        self.secret = api_secret

    def __call__(self, method: str, path: str, body: str = '', params: Dict[str, str] = None) -> Dict:
        if params:
            query_params = '&'.join([f'{k}={v}' for k, v in params.items()])
            path = f'{path}?{query_params}'

        conn = http.client.HTTPSConnection("api.coinbase.com")
        try:
            timestamp = str(int(time.time()))
            message = timestamp + method.upper() + \
                path.split('?')[0] + str(body)
            signature = hmac.new(self.secret.encode(
                'utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

            headers = {
                "accept": "application/json",
                "CB-ACCESS-KEY": self.key,
                "CB-ACCESS-SIGN": signature,
                "CB-ACCESS-TIMESTAMP": timestamp
            }

            conn.request(method, path, body, headers)
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
        finally:
            conn.close()
