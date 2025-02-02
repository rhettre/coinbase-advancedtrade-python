"""Unit tests for the AccountService class."""

import unittest
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime

from coinbase.rest import RESTClient
from coinbase_advanced_trader.services.account_service import AccountService


class TestAccountService(unittest.TestCase):
    """Test cases for the AccountService class."""

    def setUp(self):
        """Set up the test environment."""
        self.rest_client_mock = Mock(spec=RESTClient)
        self.account_service = AccountService(self.rest_client_mock)

    def test_get_accounts_cache(self):
        """Test the caching behavior of _get_accounts method."""
        mock_response = {
            'accounts': [
                {
                    'uuid': 'abc123',
                    'currency': 'BTC',
                    'available_balance': {'value': '1.5', 'currency': 'BTC'}
                },
                {
                    'uuid': 'def456',
                    'currency': 'ETH',
                    'available_balance': {'value': '10.0', 'currency': 'ETH'}
                }
            ]
        }
        self.rest_client_mock.get_accounts.return_value = mock_response

        # First call should fetch from API
        accounts = self.account_service._get_accounts()
        self.rest_client_mock.get_accounts.assert_called_once()
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts['BTC']['available_balance'], Decimal('1.5'))

        # Second call should use cache
        self.rest_client_mock.get_accounts.reset_mock()
        accounts = self.account_service._get_accounts()
        self.rest_client_mock.get_accounts.assert_not_called()

    def test_get_crypto_balance(self):
        """Test the get_crypto_balance method."""
        # Mock the cached accounts data
        mock_accounts = {
            'BTC': {'uuid': 'abc123', 'available_balance': Decimal('1.5')},
            'ETH': {'uuid': 'def456', 'available_balance': Decimal('10.0')}
        }
        self.account_service._get_accounts = Mock(return_value=mock_accounts)
        
        # Mock the detailed account response
        mock_detailed_account = {
            'name': 'BTC Wallet',
            'type': 'crypto',
            'active': True,
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_response = Mock()
        mock_response.account = mock_detailed_account
        self.account_service.rest_client.get_account = Mock(return_value=mock_response)
        
        btc_balance = self.account_service.get_crypto_balance('BTC')
        self.assertEqual(btc_balance, Decimal('1.5'))

        eth_balance = self.account_service.get_crypto_balance('ETH')
        self.assertEqual(eth_balance, Decimal('10.0'))

        xrp_balance = self.account_service.get_crypto_balance('XRP')
        self.assertEqual(xrp_balance, Decimal('0'))

    def test_list_held_cryptocurrencies(self):
        """Test the list_held_cryptocurrencies method."""
        mock_accounts = {
            'BTC': {'uuid': 'abc123', 'available_balance': Decimal('1.5')},
            'ETH': {'uuid': 'def456', 'available_balance': Decimal('0')},
            'XRP': {'uuid': 'ghi789', 'available_balance': Decimal('100.0')}
        }
        self.account_service._get_accounts = Mock(return_value=mock_accounts)

        held_currencies = self.account_service.list_held_crypto_balances()
        self.assertEqual(set(held_currencies), {'BTC', 'XRP'})

    @patch('coinbase_advanced_trader.services.account_service.datetime')
    def test_cache_expiration(self, mock_datetime):
        """Test the cache expiration behavior."""
        mock_response = {
            'accounts': [
                {
                    'uuid': 'abc123',
                    'currency': 'BTC',
                    'available_balance': {'value': '1.5', 'currency': 'BTC'}
                }
            ]
        }
        self.rest_client_mock.get_accounts.return_value = mock_response

        # Set initial time
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

        # First call should fetch from API
        self.account_service._get_accounts()
        self.rest_client_mock.get_accounts.assert_called_once()

        # Set time to 30 minutes later (within cache duration)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 30, 0)

        # Second call should use cache
        self.rest_client_mock.get_accounts.reset_mock()
        self.account_service._get_accounts()
        self.rest_client_mock.get_accounts.assert_not_called()

        # Set time to 61 minutes later (outside cache duration)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 13, 1, 0)

        # Third call should fetch from API again
        self.account_service._get_accounts()
        self.rest_client_mock.get_accounts.assert_called_once()

    def test_get_account_by_currency(self):
        """Test getting detailed account information by currency."""
        # Mock the cached accounts data
        mock_accounts = {
            'USD': {
                'uuid': 'abc123',
                'available_balance': Decimal('100.50')
            }
        }
        self.account_service._get_accounts = Mock(return_value=mock_accounts)
        
        # Mock the detailed account response
        mock_detailed_account = {
            'name': 'USD Wallet',
            'type': 'fiat',
            'active': True,
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_response = Mock()
        mock_response.account = mock_detailed_account
        self.account_service.rest_client.get_account = Mock(return_value=mock_response)
        
        # Test getting existing account
        account = self.account_service.get_account_by_currency('USD')
        self.assertIsNotNone(account)
        self.assertEqual(account.uuid, 'abc123')
        self.assertEqual(account.currency, 'USD')
        self.assertEqual(account.available_balance, Decimal('100.50'))
        self.assertEqual(account.name, 'USD Wallet')
        self.assertEqual(account.type, 'fiat')
        self.assertTrue(account.active)
        self.assertEqual(account.created_at, '2024-01-01T00:00:00Z')
        
        # Test getting non-existent account
        account = self.account_service.get_account_by_currency('NON_EXISTENT')
        self.assertIsNone(account)

    def test_list_payment_methods(self):
        """Test listing payment methods."""
        # Create mock payment method data
        mock_method = Mock()
        mock_method.id = 'pm123'
        mock_method.type = 'ach_bank_account'
        mock_method.name = 'Test Bank'
        mock_method.currency = 'USD'
        mock_method.allow_deposit = True
        mock_method.allow_withdraw = True
        mock_method.verified = True
        mock_method.created_at = '2024-01-01T00:00:00Z'
        mock_method.updated_at = '2024-01-02T00:00:00Z'
        
        # Mock the response
        mock_response = Mock()
        mock_response.payment_methods = [mock_method]
        self.account_service.rest_client.list_payment_methods = Mock(return_value=mock_response)
        
        # Test the method
        payment_methods = self.account_service.list_payment_methods()
        
        self.assertEqual(len(payment_methods), 1)
        pm = payment_methods[0]
        self.assertEqual(pm.id, 'pm123')
        self.assertEqual(pm.type, 'ach_bank_account')
        self.assertEqual(pm.name, 'Test Bank')
        self.assertEqual(pm.currency, 'USD')
        self.assertTrue(pm.allow_deposit)
        self.assertTrue(pm.allow_withdraw)
        self.assertTrue(pm.verified)
        self.assertEqual(pm.created_at, '2024-01-01T00:00:00Z')
        self.assertEqual(pm.updated_at, '2024-01-02T00:00:00Z')


if __name__ == '__main__':
    unittest.main()