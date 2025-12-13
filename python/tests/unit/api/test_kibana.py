import unittest
from unittest.mock import MagicMock, patch, mock_open
from sof_elk.api.kibana import KibanaClient

class TestKibanaClient(unittest.TestCase):
    def setUp(self):
        self.client = KibanaClient(host="test", port=5601)
        self.client.client = MagicMock()

    def test_find_objects(self):
        self.client.client.get.return_value.json.return_value = {"saved_objects": []}
        res = self.client.find_objects("index-pattern", fields=["title"])
        
        self.client.client.get.assert_called()
        args, kwargs = self.client.client.get.call_args
        self.assertIn("fields", kwargs['params'])
        self.assertEqual(kwargs['params']['type'], "index-pattern")
        self.assertEqual(res, {"saved_objects": []})

    def test_get_object(self):
        self.client.client.get.return_value.json.return_value = {"id": "123"}
        res = self.client.get_object("index-pattern", "123")
        self.client.client.get.assert_called_with("http://test:5601/api/saved_objects/index-pattern/123")
        self.assertEqual(res, {"id": "123"})

    def test_delete_object(self):
        self.client.client.delete.return_value.json.return_value = {"success": True}
        res = self.client.delete_object("index-pattern", "123")
        self.client.client.delete.assert_called_with("http://test:5601/api/saved_objects/index-pattern/123")
        self.assertTrue(res['success'])

    def test_import_objects(self):
        self.client.client.post.return_value.json.return_value = {"success": True}
        with patch("builtins.open", mock_open(read_data=b"data")) as mock_file:
            with patch("os.path.basename", return_value="file.ndjson"):
                res = self.client.import_objects("/path/to/file.ndjson")
                
        self.client.client.post.assert_called()
        self.assertTrue(res['success'])

    def test_get_data_views(self):
        self.client.client.get.return_value.json.return_value = {"data_views": []}
        res = self.client.get_data_views()
        self.client.client.get.assert_called_with("http://test:5601/api/data_views", params={"per_page": 10000})
        self.assertEqual(res, {"data_views": []})

if __name__ == '__main__':
    unittest.main()
