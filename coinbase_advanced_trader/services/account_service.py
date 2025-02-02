from decimal import Decimal
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from coinbase.rest import RESTClient

from coinbase_advanced_trader.logger import logger

@dataclass
class Account:
    uuid: str
    currency: str
    available_balance: Decimal
    name: str
    type: str
    active: bool
    created_at: str

@dataclass
class PaymentMethod:
    id: str
    type: str
    name: str
    currency: str
    allow_deposit: bool
    allow_withdraw: bool
    verified: bool
    created_at: str
    updated_at: Optional[str] = None

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
        """
        Get just the balance for a currency. More efficient than get_account_by_currency
        when you only need the balance.
        
        Args:
            currency: Currency code (e.g., "USD", "BTC")
            
        Returns:
            Decimal balance (0 if account not found)
        """
        try:
            account = self.get_account_by_currency(currency)
            balance = account.available_balance if account else Decimal('0')
            logger.info(f"Retrieved balance for {currency}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error retrieving balance for {currency}: {str(e)}")
            raise

    def get_account_by_currency(self, currency: str) -> Optional[Account]:
        """
        Get full account details for a currency. Uses cached data for basic info
        and makes an additional API call for detailed account information.
        
        Args:
            currency: Currency code (e.g., "USD", "BTC")
            
        Returns:
            Account object if found, None otherwise
        """
        try:
            accounts = self._get_accounts()
            if currency not in accounts:
                logger.warning(f"No account found for {currency}")
                return None
            
            # Get detailed account info using the UUID we found
            account_uuid = accounts[currency]['uuid']
            detailed_response = self.rest_client.get_account(account_uuid)
            detailed_account = detailed_response.account
            
            return Account(
                uuid=account_uuid,
                currency=currency,
                available_balance=accounts[currency]['available_balance'],
                name=detailed_account['name'],
                type=detailed_account['type'],
                active=detailed_account['active'],
                created_at=detailed_account['created_at']
            )
        except Exception as e:
            logger.error(f"Error retrieving account for {currency}: {str(e)}")
            raise

    def list_payment_methods(self) -> List[PaymentMethod]:
        """Get all payment methods without logging."""
        try:
            response = self.rest_client.list_payment_methods()
            return [
                PaymentMethod(
                    id=method.id,
                    type=method.type,
                    name=method.name,
                    currency=method.currency,
                    allow_deposit=method.allow_deposit,
                    allow_withdraw=method.allow_withdraw,
                    verified=method.verified,
                    created_at=method.created_at,
                    updated_at=method.updated_at
                )
                for method in response.payment_methods
            ]
        except Exception as e:
            logger.error(f"Error listing payment methods: {str(e)}")
            raise

    def show_deposit_methods(self) -> None:
        """Pretty print all payment methods that allow deposits."""
        try:
            methods = self.list_payment_methods()
            deposit_methods = [m for m in methods if m.allow_deposit]
            
            if not deposit_methods:
                logger.info("\nNo payment methods available for deposits")
                return
            
            logger.info(f"\nAvailable Payment Methods for Deposits:")
            for method in deposit_methods:
                logger.info(
                    f"\n  {method.name} ({method.type})"
                    f"\n  ID: {method.id}"
                    f"\n  Currency: {method.currency}"
                    f"\n  Created: {method.created_at}"
                    f"\n  ----------------------"
                )
        except Exception as e:
            logger.error(f"Error showing deposit methods: {str(e)}")
            raise

    def list_held_crypto_balances(self) -> Dict[str, Decimal]:
        """
        List all accounts with non-zero balances and their details.
        
        Returns:
            Dict mapping currency codes to their balances
        """
        try:
            accounts = self._get_accounts()
            non_zero_balances = {
                currency: account['available_balance']
                for currency, account in accounts.items()
                if account['available_balance'] > 0
            }
            
            logger.info(f"\nAccounts with Balance:")
            for currency, balance in non_zero_balances.items():
                account = accounts[currency]
                logger.info(
                    f"\n  {currency}:"
                    f"\n    Balance: {balance} {currency}"
                    f"\n    UUID: {account['uuid']}"
                    f"\n    ----------------------"
                )
            
            return non_zero_balances
        except Exception as e:
            logger.error(f"Error listing held balances: {str(e)}")
            raise