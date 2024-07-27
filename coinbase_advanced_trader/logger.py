import sys
import logging

def setup_logger():
    logger = logging.getLogger("coinbase_advanced_trader")
    logger.setLevel(logging.INFO)

    # Create a stream handler that writes to sys.stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger

logger = setup_logger()