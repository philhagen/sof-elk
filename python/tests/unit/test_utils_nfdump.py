import unittest
from unittest.mock import patch, MagicMock
from sof_elk.utils.nfdump import NfdumpManager
import sys

class TestNfdumpManager(unittest.TestCase):
    @patch("shutil.which")
    @patch("os.path.exists")
    @patch("subprocess.check_call")
    @patch("builtins.open")
    def test_process_nfdump_file(self, mock_open, mock_check_call, mock_exists, mock_which):
        mock_which.return_value = "/usr/bin/nfdump"
        # Mocks for file checks: 
        # 1. source check (True)
        # 2. dest_dir check (dir of dest file) -> True
        mock_exists.side_effect = [True, True]
        
        # is_dir check
        with patch("os.path.isdir", return_value=False):
            NfdumpManager.process_nfdump("/data/source.nfcapd", "/logstash/nfarch/out.txt")
        
        # Verify nfdump calls
        # 1. Validation call (-r source -q -c 1)
        mock_check_call.assert_any_call(["nfdump", "-r", "/data/source.nfcapd", "-q", "-c", "1"], stdout=-3, stderr=-3)
        
        # 2. Processing call
        # Mock open context manager
        mock_outfile = mock_open.return_value.__enter__.return_value
        
        expected_cmd = [
            "nfdump", "-r", "/data/source.nfcapd", "-6", "-q", "-N", "-o", 
            "fmt:0.0.0.0 " + NfdumpManager.NFDUMP_FMT
        ]
        mock_check_call.assert_any_call(expected_cmd, stdout=mock_outfile)

    @patch("shutil.which")
    def test_missing_nfdump(self, mock_which):
        mock_which.return_value = None
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                NfdumpManager.process_nfdump("src", "dst")

    @patch("shutil.which")
    @patch("os.path.exists")
    def test_missing_source(self, mock_exists, mock_which):
        mock_which.return_value = "/bin/nfdump"
        mock_exists.return_value = False
        with self.assertRaises(SystemExit):
            with patch("builtins.print"):
                NfdumpManager.process_nfdump("missing_src", "dst")
