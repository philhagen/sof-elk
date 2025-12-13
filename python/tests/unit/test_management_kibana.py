import unittest
from unittest.mock import patch, MagicMock, mock_open

# Import class under test
from sof_elk.management.kibana import KibanaManager

class TestKibanaManager(unittest.TestCase):
    @patch("sof_elk.management.kibana.Elasticsearch")
    def setUp(self, mock_es):
        self.mock_es_instance = MagicMock()
        mock_es.return_value = self.mock_es_instance
        self.mgr = KibanaManager()

    def test_wait_for_es_success(self):
        self.mock_es_instance.cluster.health.return_value = {"status": "green"}
        self.assertTrue(self.mgr._wait_for_es(max_wait=1))

    def test_wait_for_es_failure(self):
        self.mock_es_instance.cluster.health.side_effect = Exception("Connection Error")
        with patch("time.sleep"): # suppress sleep
            self.assertFalse(self.mgr._wait_for_es(max_wait=1))

    def test_load_template_component(self):
        with patch("builtins.open", mock_open(read_data='{"foo": "bar"}')):
            with patch("json.load", return_value={"foo": "bar"}):
                self.mgr._load_template("component_template", "/path/to/component-my_template.json")
                self.mock_es_instance.cluster.put_component_template.assert_called_with(name="my_template", body={"foo": "bar"})

    def test_load_template_index(self):
        with patch("builtins.open", mock_open(read_data='{"foo": "bar"}')):
             with patch("json.load", return_value={"foo": "bar"}):
                self.mgr._load_template("index_template", "/path/to/index-my_index_tpl.json")
                self.mock_es_instance.indices.put_index_template.assert_called_with(name="my_index_tpl", body={"foo": "bar"})
    
    @patch("sof_elk.api.kibana.KibanaClient")
    def test_kibana_request(self, mock_kclient_cls):
        # We test that we can perform requests via KibanaClient if we need to.
        # But _kibana_request mock method is gone. 
        # So we should test load_all which uses KibanaClient.
        pass

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("sof_elk.management.kibana.Elasticsearch") 
    @patch("sof_elk.management.kibana.KibanaManager._load_template")
    @patch("sof_elk.management.kibana.KibanaManager._wait_for_es")
    @patch("json.load")
    def test_load_all(self, mock_json_load, mock_wait, mock_load_tpl, mock_es, mock_open_file, mock_listdir, mock_exists):
        mock_wait.return_value = True
        mock_exists.return_value = True
        mock_listdir.return_value = ["test.json"]
        mock_json_load.return_value = {"foo": "bar"}
        
        # Setup KibanaClient mock
        mock_kclient = MagicMock()

        # Mock sys.modules for local import if needed, but patching the source module usually works if using 'from ...'
        # However, inside function 'from sof_elk.api.kibana import KibanaClient' 
        # implies we should patch 'sof_elk.api.kibana.KibanaClient' globally 
        # OR patch 'sof_elk.management.kibana.KibanaClient' IF it was top level.
        # Since it is inside, patching 'sof_elk.api.kibana.KibanaClient' is the way.
        
        with patch("sof_elk.api.kibana.KibanaClient", return_value=mock_kclient):
             self.mgr.load_all()
        
        # Verify KibanaClient usage
        mock_kclient.import_objects.assert_called()
        self.assertTrue(mock_load_tpl.called)

