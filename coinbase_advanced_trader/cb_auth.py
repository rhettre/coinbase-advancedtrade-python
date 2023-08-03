import http.client
import hmac
import hashlib
import json
import time
from urllib.parse import urlencode
from typing import Union, Dict


class CBAuth:
    def __init__(self, api_key, api_secret):
        self.key = api_key
        self.secret = api_secret

    def __call__(self, method: str, path: str, body: Union[Dict, str] = '', params: Dict[str, str] = None) -> Dict:
        path = self.add_query_params(path, params)
        body_encoded = self.prepare_body(body)
        headers = self.create_headers(method, path, body)

        return self.send_request(method, path, body_encoded, headers)

    def add_query_params(self, path, params):
        if params:
            query_params = urlencode(params)
            path = f'{path}?{query_params}'
        return path

    def prepare_body(self, body):
        return json.dumps(body).encode('utf-8') if body else b''

    def create_headers(self, method, path, body):
        timestamp = str(int(time.time()))
        message = timestamp + method.upper() + \
            path.split('?')[0] + (json.dumps(body) if body else '')
        signature = hmac.new(self.secret.encode(
            'utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

        return {
            "accept": "application/json",
            "CB-ACCESS-KEY": self.key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp
        }

    def send_request(self, method, path, body_encoded, headers):
        conn = http.client.HTTPSConnection("api.coinbase.com")
        try:
            conn.request(method, path, body_encoded, headers)
            res = conn.getresponse()
            data = res.read()

            if res.status == 401:
                print("Error: Unauthorized. Please check your API key and secret.")
                return None

            response_data = json.loads(data.decode("utf-8"))
            if 'error_details' in response_data and response_data['error_details'] == 'missing required scopes':
                print(
                    "Error: Missing Required Scopes. Please update your API Keys to include more permissions.")
                return None

            return response_data
        except json.JSONDecodeError:
            print("Error: Unable to decode JSON response. Raw response data:", data)
            return None
        finally:
            conn.close()
