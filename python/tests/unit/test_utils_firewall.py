import unittest
from unittest.mock import patch, MagicMock
import sys
from sof_elk.utils.firewall import FirewallManager

class TestFirewallManager(unittest.TestCase):
    @patch("shutil.which")
    @patch("os.geteuid", create=True)
    @patch("subprocess.check_call")
    def test_modify_firewall_open_tcp(self, mock_check_call, mock_geteuid, mock_which):
        mock_which.return_value = "/bin/firewall-cmd"
        mock_geteuid.return_value = 0
        
        FirewallManager.modify_firewall("open", 8080, "tcp")
        
        # Check command calls
        # 1. add port
        # 2. reload
        expected_cmd = ["firewall-cmd", "--zone=public", "--add-port=8080/tcp", "--permanent"]
        mock_check_call.assert_any_call(expected_cmd, stdout=-3) # -3 is DEVNULL
        
        mock_check_call.assert_any_call(["firewall-cmd", "--reload"], stdout=-3)

    @patch("shutil.which")
    @patch("os.geteuid", create=True)
    @patch("subprocess.check_call")
    def test_modify_firewall_close_udp(self, mock_check_call, mock_geteuid, mock_which):
        mock_which.return_value = "/bin/firewall-cmd"
        mock_geteuid.return_value = 0
        
        FirewallManager.modify_firewall("close", 514, "udp")
        
        expected_cmd = ["firewall-cmd", "--zone=public", "--remove-port=514/udp", "--permanent"]
        mock_check_call.assert_any_call(expected_cmd, stdout=-3)

    @patch("shutil.which")
    def test_firewall_cmd_missing(self, mock_which):
        mock_which.return_value = None
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                FirewallManager.modify_firewall("open", 80, "tcp")

    @patch("shutil.which")
    @patch("os.geteuid", create=True)
    def test_not_root(self, mock_geteuid, mock_which):
        mock_which.return_value = "/bin/firewall-cmd"
        mock_geteuid.return_value = 1000
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                FirewallManager.modify_firewall("open", 80, "tcp")
