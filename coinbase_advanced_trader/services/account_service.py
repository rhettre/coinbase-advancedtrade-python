from decimal import Decimal
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from coinbase.rest import RESTClient

from coinbase_advanced_trader.logger import logger

class AccountService:
    """Service for handling account-related operations."""

    def __init__(self, rest_client: RESTClient):
        self.rest_client = rest_client
        self._accounts_cache = None
        self._cache_timestamp = None
        self._cache_duration = timedelta(hours=1)

    def _get_accounts(self, limit: int = 250) -> Dict[str, Dict[str, Any]]:
        if self._accounts_cache is None or \
        (datetime.now() - self._cache_timestamp) > self._cache_duration:
            logger.info("Fetching fresh account data from Coinbase")
            response = self.rest_client.get_accounts(limit=limit)
            self._accounts_cache = {
                account['currency']: {
                    'uuid': account['uuid'],
                    'available_balance': Decimal(account['available_balance']['value'])
                }
                for account in response['accounts']
            }
            logger.debug(f"Processed accounts cache: {self._accounts_cache}")
            self._cache_timestamp = datetime.now()
        return self._accounts_cache

    def get_crypto_balance(self, currency: str) -> Decimal:
        try:
            accounts = self._get_accounts()
            if currency not in accounts:
                logger.warning(f"No account found for {currency}")
                return Decimal('0')
            balance = accounts[currency]['available_balance']
            logger.info(f"Retrieved balance for {currency}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error retrieving balance for {currency}: {str(e)}")
            raise

    def list_held_crypto_balances(self) -> Dict[str, Decimal]:
        """
        Get a dictionary of all held cryptocurrencies and their balances.
        Returns:
            Dict[str, Decimal]: A dictionary where the key is the currency code
            and the value is the balance as a Decimal.
        """
        accounts = self._get_accounts()
        non_zero_balances = {
            currency: account['available_balance']
            for currency, account in accounts.items()
            if account['available_balance'] > 0
        }
        
        logger.info(f"Found {len(non_zero_balances)} non-zero balances:")
        for currency, balance in non_zero_balances.items():
            logger.info(f"{currency}: {balance}")
        
        return non_zero_balances