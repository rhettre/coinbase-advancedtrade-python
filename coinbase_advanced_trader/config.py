# Default price multipliers for limit orders
BUY_PRICE_MULTIPLIER = 0.9995
SELL_PRICE_MULTIPLIER = 1.005

# Default schedule for the trade_based_on_fgi function
FGI_SCHEDULE = [
    {'threshold': 10, 'factor': 1.5, 'action': 'buy'},
    {'threshold': 20, 'factor': 1.3, 'action': 'buy'},
    {'threshold': 30, 'factor': 1.1, 'action': 'buy'},
    {'threshold': 70, 'factor': 0.9, 'action': 'sell'},
    {'threshold': 80, 'factor': 0.7, 'action': 'sell'},
    {'threshold': 90, 'factor': 0.5, 'action': 'sell'}
]

# API endpoints
FEAR_AND_GREED_API_URL = 'https://api.alternative.me/fng/?limit=1'

# Logging configuration
LOG_FILE_PATH = 'coinbase_advanced_trader.log'
LOG_LEVEL = 'DEBUG'