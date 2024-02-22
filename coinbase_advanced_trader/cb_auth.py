import http.client
import json
from urllib.parse import urlencode
from typing import Union, Dict
import jwt
from cryptography.hazmat.primitives import serialization
import time


class CBAuth:
    """
    Singleton class for Coinbase authentication.
    """

    _instance = None  # Class attribute to hold the singleton instance

    def __new__(cls):
        """
        Override the __new__ method to control the object creation process.
        :return: A single instance of CBAuth
        """
        if cls._instance is None:
            print("Authenticating with Coinbase")
            cls._instance = super(CBAuth, cls).__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        """
        Initialize the CBAuth instance with API credentials.
        """
        self.key = None
        self.secret = None

    def set_credentials(self, api_key, api_secret):
        """
        Update the API credentials used for authentication.
        :param api_key: The API Key for Coinbase API
        :param api_secret: The API Secret for Coinbase API
        """
        self.key = api_key
        self.secret = api_secret

    def __call__(
        self,
        method: str,
        path: str,
        body: Union[Dict, str] = "",
        params: Dict[str, str] = None,
    ) -> Dict:
        """
        Prepare and send an authenticated request to the Coinbase API.

        :param method: HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE)
        :param path: API endpoint path
        :param body: Request payload
        :param params: URL parameters
        :return: Response from the Coinbase API as a dictionary
        """
        request_path = self.add_query_params(path, params)
        body_encoded = self.prepare_body(body)

        uri = f"{method} api.coinbase.com{request_path}"
        jwt_token = self.build_jwt("retail_rest_api_proxy",uri)

        headers = {"Authorization": f"Bearer {jwt_token}"}

        return self.send_request(method, path, body_encoded, headers)

    def add_query_params(self, path, params):
        if params:
            query_params = urlencode(params)
            path = f"{path}?{query_params}"
        return path

    def prepare_body(self, body):
        return json.dumps(body).encode("utf-8") if body else b""

    def build_jwt(self, service, uri):
        private_key_bytes = self.secret.encode("utf-8")
        private_key = serialization.load_pem_private_key(
            private_key_bytes, password=None
        )

        jwt_payload = {
            "sub": self.key,
            "iss": "coinbase-cloud",
            "nbf": int(time.time()),
            "exp": int(time.time()) + 60,
            "aud": [service],
            "uri": uri,
        }

        jwt_token = jwt.encode(
            jwt_payload,
            private_key,
            algorithm="ES256",
            headers={"kid": self.key, "nonce": str(int(time.time()))},
        )

        return jwt_token

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
            if (
                "error_details" in response_data
                and response_data["error_details"] == "missing required scopes"
            ):
                print(
                    "Error: Missing Required Scopes. Please update your API Keys to include more permissions."
                )
                return None

            return response_data
        except json.JSONDecodeError:
            print("Error: Unable to decode JSON response. Raw response data:", data)
            return None
        finally:
            conn.close()
