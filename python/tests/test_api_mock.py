import unittest
from unittest.mock import MagicMock, patch
from sof_elk.api.client import SOFElkSession, SOFElkHTTPClient, SOFElkResponseError
from sof_elk.api.kibana import KibanaClient
import requests

class TestSOFElkAPI(unittest.TestCase):
    def test_client_retry_logic(self):
        # We can't easily test retry logic without a real socket or complex mocking of urllib3
        # But we can test that the session is created with adapters.
        client = SOFElkSession.get_session()
        self.assertIsInstance(client, SOFElkHTTPClient)
        self.assertIsNotNone(client._session.adapters['http://'])
        
    @patch('requests.Session.request')
    def test_kibana_find_objects(self, mock_request):
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"saved_objects": []}
        mock_request.return_value = mock_response
        
        kb = KibanaClient()
        kb.find_objects("dashboard")
        
        # Check that proper params and headers were sent
        args, kwargs = mock_request.call_args
        self.assertIn("http://localhost:5601/api/saved_objects/_find", args)
        self.assertEqual(kwargs['params']['type'], 'dashboard')
        self.assertEqual(kb.client._session.headers['kbn-xsrf'], 'true')

    @patch('requests.Session.request')
    def test_kibana_error_handling(self, mock_request):
        # Simulate 404
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_request.return_value = mock_response
        
        kb = KibanaClient()
        with self.assertRaises(SOFElkResponseError):
            kb.get_object("dashboard", "non-existent")

if __name__ == '__main__':
    unittest.main()
