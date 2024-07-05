import logging
import sys
from coinbase_advanced_trader.config import config_manager


def setup_logger():
    """
    Set up and configure the logger for the Coinbase Advanced Trader application.

    Returns:
        logging.Logger: Configured logger instance.
    """
    log_file_path = config_manager.get('LOG_FILE_PATH')
    log_level = config_manager.get('LOG_LEVEL')

    logger = logging.getLogger('coinbase_advanced_trader')
    logger.setLevel(getattr(logging, log_level))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()