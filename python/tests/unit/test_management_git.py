import unittest
from unittest.mock import patch, MagicMock
import os
from sof_elk.management.git import GitManager

class TestGitManager(unittest.TestCase):
    @patch("subprocess.run")
    def test_check_pull_needed_update_avail(self, mock_run):
        mock_run.side_effect = [
            MagicMock(stdout="hash1"), # local
            MagicMock(stdout="hash2"), # remote
            MagicMock(stdout="hash1"), # base
        ]
        
        with patch("builtins.print") as mock_print:
            GitManager.check_pull_needed()
            self.assertTrue(any("Upstream Updates Available" in str(c) for c in mock_print.call_args_list))

    @patch("subprocess.run")
    def test_check_pull_needed_uptodate(self, mock_run):
        mock_run.side_effect = [
            MagicMock(stdout="hash1"), # local
            MagicMock(stdout="hash1"), # remote
            MagicMock(stdout="hash1"), # base
        ]
        with patch("builtins.print") as mock_print:
            GitManager.check_pull_needed()
            self.assertFalse(mock_print.called)

    @patch("subprocess.run")
    def test_update_cli(self, mock_run):
        mock_run.side_effect = [
            MagicMock(stdout=""), # status
            MagicMock(return_code=0), # remote update
            MagicMock(stdout="hash1"), # local
            MagicMock(stdout="hash2"), # remote
            MagicMock(stdout="hash1"), # base
            MagicMock(), # reset
            MagicMock(), # clean
            MagicMock(), # pull
            MagicMock(), # remote update
            MagicMock(stdout="1234"), # pgrep
            MagicMock(), # kill
        ]
        
        # Patch require_root to bypass (though now safe on windows, explicit patch is safer for test logic)
        with patch.object(GitManager, "require_root"):
            with patch("builtins.print") as mock_print:
                GitManager.update_cli()
                pass

    @patch("subprocess.run")
    def test_branch_cli_switch(self, mock_run):
        mock_run.side_effect = [
             MagicMock(stdout="refs/heads/testbranch"), # ls-remote
             MagicMock(stdout=""), # status
             MagicMock(), # reset
             MagicMock(), # set-branches
             MagicMock(), # fetch
             MagicMock(), # checkout
        ]
        
        with patch.object(GitManager, "require_root"):
            with patch("builtins.input", return_value=""):
                 with patch("builtins.print"):
                     GitManager.branch_cli("testbranch")
        
        self.assertTrue(mock_run.called)
