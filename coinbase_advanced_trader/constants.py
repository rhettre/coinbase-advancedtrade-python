"""Constants and default configuration for the Coinbase Advanced Trader."""

DEFAULT_CONFIG = {
    'BUY_PRICE_MULTIPLIER': 0.9995,
    'SELL_PRICE_MULTIPLIER': 1.005,
    'FEAR_AND_GREED_API_URL': 'https://api.alternative.me/fng/?limit=1',
    'LOG_FILE_PATH': 'coinbase_advanced_trader.log',
    'LOG_LEVEL': 'DEBUG',
    'FGI_CACHE_DURATION': 3600
}