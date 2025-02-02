import unittest
from unittest.mock import Mock
from coinbase_advanced_trader.services.funds_service import FundsService

class TestFundsService(unittest.TestCase):
    def setUp(self):
        self.rest_client = Mock()
        self.funds_service = FundsService(self.rest_client)

    def test_deposit_fiat(self):
        """Test fiat deposit functionality."""
        # Mock successful deposit response
        mock_response = {
            'data': {
                'id': 'dep123',
                'status': 'pending',
                'amount': {'amount': '25.00'},
                'user_reference': 'test_deposit',
                'instant': False,
                'committed': True
            }
        }
        self.rest_client.post = Mock(return_value=mock_response)
        
        # Test deposit
        response = self.funds_service.deposit_fiat(
            account_id='acc123',
            payment_method_id='pm123',
            amount='25.00',
            currency='USD'
        )
        
        # Verify the response
        self.assertEqual(response['data']['id'], 'dep123')
        self.assertEqual(response['data']['amount']['amount'], '25.00')
        
        # Verify the API call
        self.rest_client.post.assert_called_once()
        args, kwargs = self.rest_client.post.call_args
        self.assertEqual(args[0], '/v2/accounts/acc123/deposits')
        self.assertEqual(kwargs['data']['amount'], '25.00')
        self.assertEqual(kwargs['data']['currency'], 'USD')
        self.assertEqual(kwargs['data']['payment_method'], 'pm123')
        self.assertEqual(kwargs['data']['commit'], True) 