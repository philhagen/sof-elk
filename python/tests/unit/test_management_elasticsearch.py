import unittest
from unittest.mock import patch, MagicMock

# Import the class under test
from sof_elk.management.elasticsearch import ElasticsearchManager

class TestElasticsearchManager(unittest.TestCase):
    @patch("sof_elk.management.elasticsearch.ElasticsearchManagement")
    @patch("sof_elk.management.elasticsearch.get_es_client")
    def setUp(self, mock_get_client, mock_mgmt):
        self.mock_es_instance = MagicMock()
        mock_get_client.return_value = self.mock_es_instance
        self.mgr = ElasticsearchManager()

    def test_get_indices(self):
        # Setup mock return for get_alias
        self.mock_es_instance.indices.get_alias.return_value = {
            "logstash-2023.01.01": {},
            "netflow-2023.01.01": {},
            ".kibana": {}
        }
        
        indices = self.mgr.get_indices()
        self.assertIn("logstash", indices)
        self.assertIn("netflow", indices)
        self.assertNotIn(".kibana", indices)

    def test_freeze_index(self):
        # Setup mock for get (called inside freeze_index)
        self.mock_es_instance.indices.get.return_value = {
            "logstash-2023.01.01": {}
        }
        
        with patch("builtins.print"):
            self.mgr.freeze_index("logstash-*")
        
        # Verify calls
        self.mock_es_instance.indices.put_settings.assert_called() # read only, etc
        self.mock_es_instance.indices.clone.assert_called()
        self.mock_es_instance.indices.close.assert_called()

    def test_thaw_index(self):
        with patch("builtins.print"):
            self.mgr.thaw_index("frozen-index")
        
        self.mock_es_instance.indices.open.assert_called_with(index="frozen-index")
        self.mock_es_instance.indices.put_settings.assert_called_with(index="frozen-index", body='{ "hidden": null }')

    def test_clear_cli_nukeitall(self):
        self.mock_es_instance.indices.get_alias.return_value = {"logstash-2023.01.01": {}}
        self.mock_es_instance.count.return_value = {"count": 100}
        
        # Mock confirm to return true
        with patch.object(self.mgr, "confirm", return_value=True) as mock_confirm:
            with patch("builtins.print"):
                self.mgr.clear_cli(nukeitall=True)
        
        self.mock_es_instance.indices.delete.assert_called()

    @patch("subprocess.check_call")
    @patch("subprocess.call")
    @patch("builtins.open")
    @patch("json.load")
    @patch("json.dump")
    @patch("os.path.exists")
    @patch("os.geteuid", create=True)
    def test_reload_registry(self, mock_geteuid, mock_exists, mock_dump, mock_load, mock_open, mock_call, mock_check_call):
        mock_geteuid.return_value = 0
        mock_exists.return_value = True
        
        # specific mock for json load
        mock_load.return_value = [
            {"source": "/logstash/syslog/file1.log", "offset": 100},
            {"source": "/logstash/netflow/file2.log", "offset": 200}
        ]
        
        with patch("builtins.print"):
            self.mgr.reload_registry(match_path="/logstash/syslog/")
        
        # Verify stop called
        mock_check_call.assert_called_with(["systemctl", "stop", "filebeat"])
        
        # Verify dump called with filtered list
        expected_dump = [{"source": "/logstash/netflow/file2.log", "offset": 200}]
        mock_dump.assert_called()
        args, _ = mock_dump.call_args
        self.assertEqual(args[0], expected_dump)
        
        # Verify start called
        mock_call.assert_called_with(["systemctl", "start", "filebeat"])

    def test_clear_cli_index(self):
        self.mock_es_instance.count.return_value = {"count": 100}
        with patch.object(self.mgr, "confirm", return_value=True):
             with patch("builtins.print"):
                 self.mgr.clear_cli(index="netflow")
        
        self.mock_es_instance.indices.delete.assert_called_with(index="netflow-*", ignore=[400, 404])

    def test_clear_cli_filepath(self):
        self.mock_es_instance.count.return_value = {"count": 100}
        with patch.object(self.mgr, "confirm", return_value=True):
             with patch("builtins.print"):
                 # Use a path that maps to a known index in SOURCEDIR_INDEX_MAPPING
                 self.mgr.clear_cli(filepath="/logstash/syslog/somefile")
        
        # syslog maps to logstash
        self.mock_es_instance.delete_by_query.assert_called_with(
            index="logstash-*",
            body={"query": {"prefix": {"source.keyword": "/logstash/syslog/somefile"}}}
        )

    def test_freeze_index_options(self):
         self.mock_es_instance.indices.get.return_value = {
            "logstash-2023.01.01": {}
        }
         with patch("builtins.print"):
            self.mgr.freeze_index("logstash-*", delete_source=True, newindex="myfrozenindex")
         
         # Check clone target
         self.mock_es_instance.indices.clone.assert_called_with(
             index="logstash-2023.01.01", 
             target="myfrozenindex", 
             body=ElasticsearchManager.CLONE_SETTINGS
         )
         # Check delete source
         self.mock_es_instance.indices.delete.assert_called_with(index="logstash-2023.01.01")
