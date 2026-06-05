from decimal import Decimal
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from coinbase.rest import RESTClient

from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.utils import ensure_dict, get_response_value

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
        self._accounts_cache = {}
        self._cache_timestamp = {}
        self._cache_duration = timedelta(hours=1)

    def _get_accounts(
        self,
        limit: int = 250,
        retail_portfolio_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        cache_key = retail_portfolio_id or "__default__"
        cache_timestamp = self._cache_timestamp.get(cache_key)
        if cache_key not in self._accounts_cache or \
        cache_timestamp is None or \
        (datetime.now() - cache_timestamp) > self._cache_duration:
            logger.info("Fetching fresh account data from Coinbase")
            account_kwargs: Dict[str, Any] = {"limit": limit}
            if retail_portfolio_id:
                account_kwargs["retail_portfolio_id"] = retail_portfolio_id
            response = self.rest_client.get_accounts(**account_kwargs)
            response_dict = ensure_dict(response)
            self._accounts_cache[cache_key] = {
                account['currency']: {
                    'uuid': account['uuid'],
                    'available_balance': Decimal(account['available_balance']['value'])
                }
                for account in response_dict.get('accounts', [])
            }
            logger.debug(f"Processed accounts cache: {self._accounts_cache[cache_key]}")
            self._cache_timestamp[cache_key] = datetime.now()
        return self._accounts_cache[cache_key]

    def get_crypto_balance(
        self,
        currency: str,
        retail_portfolio_id: Optional[str] = None
    ) -> Decimal:
        """
        Get just the balance for a currency. More efficient than get_account_by_currency
        when you only need the balance.
        
        Args:
            currency: Currency code (e.g., "USD", "BTC")
            retail_portfolio_id: Optional Coinbase portfolio UUID to scope the balance.
            
        Returns:
            Decimal balance (0 if account not found)
        """
        try:
            account = self.get_account_by_currency(
                currency,
                retail_portfolio_id=retail_portfolio_id
            )
            balance = account.available_balance if account else Decimal('0')
            logger.info(f"Retrieved balance for {currency}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error retrieving balance for {currency}: {str(e)}")
            raise

    def get_account_by_currency(
        self,
        currency: str,
        retail_portfolio_id: Optional[str] = None
    ) -> Optional[Account]:
        """
        Get full account details for a currency. Uses cached data for basic info
        and makes an additional API call for detailed account information.
        
        Args:
            currency: Currency code (e.g., "USD", "BTC")
            retail_portfolio_id: Optional Coinbase portfolio UUID to scope the lookup.
            
        Returns:
            Account object if found, None otherwise
        """
        try:
            accounts = self._get_accounts(retail_portfolio_id=retail_portfolio_id)
            if currency not in accounts:
                logger.warning(f"No account found for {currency}")
                return None
            
            # Get detailed account info using the UUID we found
            account_uuid = accounts[currency]['uuid']
            detailed_response = self.rest_client.get_account(account_uuid)
            detailed_account = ensure_dict(detailed_response).get('account', {})
            
            return Account(
                uuid=account_uuid,
                currency=currency,
                available_balance=accounts[currency]['available_balance'],
                name=get_response_value(detailed_account, 'name'),
                type=get_response_value(detailed_account, 'type'),
                active=get_response_value(detailed_account, 'active'),
                created_at=get_response_value(detailed_account, 'created_at')
            )
        except Exception as e:
            logger.error(f"Error retrieving account for {currency}: {str(e)}")
            raise

    def list_payment_methods(self) -> List[PaymentMethod]:
        """Get all payment methods without logging."""
        try:
            response = self.rest_client.list_payment_methods()
            response_dict = ensure_dict(response)
            return [
                PaymentMethod(
                    id=get_response_value(method, 'id'),
                    type=get_response_value(method, 'type'),
                    name=get_response_value(method, 'name'),
                    currency=get_response_value(method, 'currency'),
                    allow_deposit=get_response_value(method, 'allow_deposit'),
                    allow_withdraw=get_response_value(method, 'allow_withdraw'),
                    verified=get_response_value(method, 'verified'),
                    created_at=get_response_value(method, 'created_at'),
                    updated_at=get_response_value(method, 'updated_at')
                )
                for method in response_dict.get('payment_methods', [])
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

    def list_held_crypto_balances(
        self,
        retail_portfolio_id: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """
        List all accounts with non-zero balances and their details.
        
        Returns:
            Dict mapping currency codes to their balances
        """
        try:
            accounts = self._get_accounts(retail_portfolio_id=retail_portfolio_id)
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
