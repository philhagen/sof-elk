import unittest
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from sof_elk.api.client import SOFElkSession
from sof_elk.api.elasticsearch import ElasticsearchManagement

class TestAPIUseCases(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('requests.Session.get')
    def test_case_1_download_file(self, mock_get):
        """
        Test streaming file download.
        """
        # Mock response with iter_content
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
        mock_response.headers = {}
        # Enter context manager
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        
        mock_get.return_value = mock_response
        
        client = SOFElkSession.get_session()
        target = os.path.join(self.test_dir, "test_download.bin")
        
        client.download_file("http://example.com/file", target)
        
        with open(target, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'chunk1chunk2')

    @patch('elasticsearch.client.IndicesClient.forcemerge')
    def test_case_2_force_merge(self, mock_forcemerge):
        """
        Test force merge wrapper.
        """
        mgmt = ElasticsearchManagement(es_client=MagicMock())
        # We need to dig into the .es object if we passed a mock, or mock the internal
        # Actually easier to mock the ES client passed in
        es_mock = MagicMock()
        mgmt = ElasticsearchManagement(es_client=es_mock)
        
        mgmt.force_merge("logstash-*", only_expunge_deletes=True)
        es_mock.indices.forcemerge.assert_called_with(index="logstash-*", params={'only_expunge_deletes': 'true'})

    @patch('elasticsearch.client.CatClient.indices')
    def test_case_3_cat_indices(self, mock_cat):
        """
        Test cat indices.
        """
        es_mock = MagicMock()
        mgmt = ElasticsearchManagement(es_client=es_mock)
        
        mgmt.list_indices("logstash-*")
        es_mock.cat.indices.assert_called_with(index="logstash-*", format="json", v=True)

if __name__ == '__main__':
    unittest.main()
