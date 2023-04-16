API_KEY = None
API_SECRET = None


def set_api_credentials(api_key, api_secret):
    global API_KEY
    global API_SECRET

    API_KEY = api_key
    API_SECRET = api_secret
