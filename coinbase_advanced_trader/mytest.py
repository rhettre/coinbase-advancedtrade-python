from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient

api_key = "organizations/fe354ade-30a3-4ec5-bf73-7c812e36b7d9/apiKeys/b7c0c86a-5f63-4084-8a1d-1b58f27af99a"
api_secret = "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIJYaay8Eg242/p32h26VD9YOvjwhPIuvShhrCYj4DJEloAoGCCqGSM49\nAwEHoUQDQgAEwUKlwyWkQ/M82sfh0zCLm6VFScmsrP/FlywQyga88nI6CQwPgEDs\no/HbL+JyEP7GKwLgQ9/y3mbGZTp9csYW4A==\n-----END EC PRIVATE KEY-----\n"

client = EnhancedRESTClient(api_key=api_key, api_secret=api_secret)

# Perform a market buy
client.fiat_market_buy("DOGE-USD", "1")