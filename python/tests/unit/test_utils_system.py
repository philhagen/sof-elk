import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from sof_elk.utils.system import SystemManager

class TestSystemManager(unittest.TestCase):
    @patch("os.geteuid", create=True)
    def test_not_root(self, mock_geteuid):
        mock_geteuid.return_value = 1000
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                SystemManager.change_keyboard("us")

    @patch("os.geteuid", create=True)
    @patch("subprocess.check_call")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='XKBLAYOUT="gb"')
    def test_change_keyboard_success(self, mock_file_open, mock_exists, mock_check_call, mock_geteuid):
        mock_geteuid.return_value = 0
        mock_exists.return_value = True
        
        with patch("builtins.print"):
            SystemManager.change_keyboard("us")
        
        mock_check_call.assert_called_with(["loadkeys", "us"], stdout=-3)
        mock_file_open.assert_called_with(SystemManager.KEYBOARD_DEFAULT_FILE, 'w')
        
        # Checking write content is tricky with simple mock_open/writelines but ensures it was called
        handle = mock_file_open()
        handle.writelines.assert_called()

    @patch("os.geteuid", create=True)
    @patch("subprocess.check_call")
    def test_loadkeys_failure(self, mock_check_call, mock_geteuid):
        mock_geteuid.return_value = 0
        import subprocess
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "loadkeys")
        
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                SystemManager.change_keyboard("bad")
