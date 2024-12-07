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
        mock_accounts = {
            'BTC': {'uuid': 'abc123', 'available_balance': Decimal('1.5')},
            'ETH': {'uuid': 'def456', 'available_balance': Decimal('10.0')}
        }
        self.account_service._get_accounts = Mock(return_value=mock_accounts)

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


if __name__ == '__main__':
    unittest.main()