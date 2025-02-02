# <ai_context>
# New module implementing fiat deposit and withdrawal functionality using
# the enhanced authentication approach from coinbase-advanced-py (ECDSA).
# This code replaces the old scripts from 'coinbase_deposit.py' and
# 'coinbase_withdrawals.py', removing any legacy authentication references.
# </ai_context>

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class FundsService:
    """
    A service class providing fiat deposit functionality,
    implemented using the same authentication mechanism as the EnhancedRESTClient.
    """

    def __init__(self, rest_client):
        """
        Args:
            rest_client: The EnhancedRESTClient instance used for making
                         authenticated requests.
        """
        self.rest_client = rest_client
        self._base_url_v2 = "/v2"

    def deposit_fiat(self, account_id: str, payment_method_id: str,
                     amount: str, currency: str = "USD",
                     commit: bool = True,
                     log_response: bool = True) -> Dict[str, Any]:
        """
        Deposits a specified fiat amount into a Coinbase fiat account.

        Args:
            account_id: The Coinbase account ID to deposit into.
            payment_method_id: The payment method ID (e.g. bank). Will be sent as 'payment_method'.
            amount: The amount to deposit.
            currency: The fiat currency code (default "USD").
            commit: Whether to commit immediately (default True).
            log_response: Whether to log the response details (default True).

        Returns:
            Dict containing the deposit response data.
        """
        endpoint = f"{self._base_url_v2}/accounts/{account_id}/deposits"
        logger.info(
            f"\nInitiating Deposit:"
            f"\n  Account: {account_id}"
            f"\n  Payment Method: {payment_method_id}"
            f"\n  Amount: {amount} {currency}"
            f"\n  Commit: {commit}"
        )
        
        data = {
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method_id,
            "commit": commit
        }
        
        try:
            response = self.rest_client.post(endpoint, data=data)
            
            if log_response:
                deposit_data = response.get('data', {})
                fee_details = deposit_data.get('fee', {})
                native_amount = deposit_data.get('native_amount', {})
                
                logger.info(
                    f"\nDeposit Response:"
                    f"\n  Transaction ID: {deposit_data.get('id')}"
                    f"\n  Status: {deposit_data.get('status')}"
                    f"\n  Amount:"
                    f"\n    Requested: {deposit_data.get('amount', {}).get('amount')} {currency}"
                    f"\n    Native: {native_amount.get('amount')} {native_amount.get('currency')}"
                    f"\n  Fee: {fee_details.get('amount')} {fee_details.get('currency')}"
                    f"\n  Reference: {deposit_data.get('user_reference')}"
                    f"\n  Details:"
                    f"\n    Instant: {deposit_data.get('instant')}"
                    f"\n    Committed: {deposit_data.get('committed')}"
                    f"\n    Created At: {deposit_data.get('created_at')}"
                    f"\n    Updated At: {deposit_data.get('updated_at')}"
                    f"\n    Payout At: {deposit_data.get('payout_at')}"
                )
                
                logger.info(
                    f"\nFull Response Payload:\n"
                    f"{json.dumps(response, indent=2, sort_keys=True)}"
                )
            return response
            
        except Exception as e:
            logger.error(
                f"\nDeposit Failed:"
                f"\n  Error: {str(e)}"
                f"\n  Account: {account_id}"
                f"\n  Amount: {amount} {currency}"
            )
            raise