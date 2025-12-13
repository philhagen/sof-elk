import unittest
from unittest.mock import patch, MagicMock
from sof_elk.management.logstash import LogstashManager
import sys

class TestLogstashManager(unittest.TestCase):
    @patch("shutil.which")
    @patch("os.path.exists")
    @patch("os.geteuid", create=True)
    @patch("subprocess.check_call")
    def test_update_plugins_all_success(self, mock_check_call, mock_geteuid, mock_exists, mock_which):
        mock_geteuid.return_value = 0
        mock_exists.return_value = True # binary exists
        
        with patch("builtins.print"):
             LogstashManager.update_plugins()
        
        # Verify check_call was called for each plugin
        self.assertEqual(mock_check_call.call_count, len(LogstashManager.PLUGINS))
        args, _ = mock_check_call.call_args_list[0]
        self.assertEqual(args[0][0], LogstashManager.LOGSTASH_PLUGIN_BIN)
        self.assertEqual(args[0][1], "install")

    @patch("shutil.which")
    @patch("os.path.exists")
    @patch("os.geteuid", create=True)
    @patch("subprocess.check_call")
    def test_update_plugins_one_failure(self, mock_check_call, mock_geteuid, mock_exists, mock_which):
        mock_geteuid.return_value = 0
        mock_exists.return_value = True
        
        # Make one call fail, others succeed
        import subprocess
        mock_check_call.side_effect = [subprocess.CalledProcessError(1, "cmd")] + [None] * (len(LogstashManager.PLUGINS) - 1)
        
        with patch("builtins.print"):
             LogstashManager.update_plugins()
        
        # Should continue to try all
        self.assertEqual(mock_check_call.call_count, len(LogstashManager.PLUGINS))

    @patch("os.path.exists")
    @patch("os.geteuid", create=True)
    def test_binary_not_found(self, mock_geteuid, mock_exists):
        mock_geteuid.return_value = 0
        mock_exists.return_value = False
        with patch("shutil.which", return_value=None):
             with self.assertRaises(SystemExit):
                 with patch("builtins.print"):
                     LogstashManager.update_plugins()

    @patch("os.geteuid", create=True)
    def test_not_root(self, mock_geteuid):
        mock_geteuid.return_value = 1000
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                LogstashManager.update_plugins()
