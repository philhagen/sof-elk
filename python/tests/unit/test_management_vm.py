import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from sof_elk.management.vm import VMManager

class TestVMManager(unittest.TestCase):
    @patch("os.path.exists")
    def test_check_update_already_exists(self, mock_exists):
        mock_exists.return_value = True
        VMManager.check_update()
        # Should return immediately, no calls
        # (Implicitly verified by no other mocks needed)

    @patch("os.path.exists")
    @patch("os.path.isdir")
    @patch("subprocess.check_output")
    def test_check_update_not_public_branch(self, mock_check, mock_isdir, mock_exists):
        mock_exists.return_value = False
        mock_isdir.return_value = True
        mock_check.return_value = "feature/foobar"
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            VMManager.check_update()
            mock_urlopen.assert_not_called()

    @patch("sof_elk.management.vm.SOFElkSession")
    @patch("subprocess.check_output")
    def test_check_update_available(self, mock_subprocess, mock_session_cls):
        mock_subprocess.return_value = "public/v20230101"
        
        mock_client = MagicMock()
        mock_session_cls.get_session.return_value = mock_client
        
        # Mock response
        mock_resp = MagicMock()
        mock_resp.url = "https://example.com/v20230202" # Newer version
        mock_client.head.return_value = mock_resp

        with patch("builtins.open", mock_open()) as mock_file:
            VMManager.check_update()
            
            # Should open file to write flag
            mock_file.assert_called_with(VMManager.VM_UPDATE_STATUS_FILE, 'w')

    @patch("sof_elk.management.vm.SOFElkSession")
    @patch("subprocess.check_output")
    def test_check_update_uptodate(self, mock_subprocess, mock_session_cls):
        mock_subprocess.return_value = "public/v20230101"
        
        mock_client = MagicMock()
        mock_session_cls.get_session.return_value = mock_client
        
        mock_resp = MagicMock()
        mock_resp.url = "https://example.com/v20230101" # Same version
        mock_client.head.return_value = mock_resp

        with patch("builtins.open", mock_open()) as mock_file:
            VMManager.check_update()
            
            # Should NOT open file
            assert not mock_file.called
