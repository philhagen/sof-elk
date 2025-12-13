import unittest
from unittest.mock import patch, MagicMock
from sof_elk.utils.login import LoginManager

class TestLoginManager(unittest.TestCase):
    @patch("sof_elk.utils.login.GitManager")
    @patch("subprocess.run")
    @patch("subprocess.check_output")
    @patch("platform.system")
    def test_show_login_message(self, mock_platform, mock_check, mock_run, mock_git):
        mock_run.return_value = MagicMock(returncode=0, stdout="Ubuntu 22.04")
        mock_check.return_value = "GNU/Linux"
        
        with patch("builtins.print"):
            LoginManager.show_login_message()
            
        mock_git.check_pull_needed.assert_called()
        
    @patch("sof_elk.utils.login.GitManager")
    @patch("subprocess.run")
    def test_show_login_message_lsb_fail(self, mock_run, mock_git):
        mock_run.return_value = MagicMock(returncode=1)
        
        with patch("builtins.open", unittest.mock.mock_open(read_data='DISTRIB_DESCRIPTION="My Distro"')):
             with patch("os.path.exists", return_value=True):
                 with patch("builtins.print"):
                     LoginManager.show_login_message()
        
        # Assertions implicit - shouldn't crash
        mock_git.check_pull_needed.assert_called()
