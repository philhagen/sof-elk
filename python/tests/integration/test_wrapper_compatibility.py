import sys
from unittest.mock import patch, MagicMock

# Mock ES if not present
if "elasticsearch" not in sys.modules:
    sys.modules["elasticsearch"] = MagicMock()

import unittest
from sof_elk.management.cli import register_subcommand as register_mgmt
from sof_elk.management.git import GitManager
import argparse

class TestWrapperCompatibility(unittest.TestCase):
    """
    Test that CLI arguments map correctly to underlying functions, mimicking wrapper behavior.
    """
    
    def setUp(self):
        self.parser = argparse.ArgumentParser()
        subparsers = self.parser.add_subparsers(dest="command")
        register_mgmt(subparsers)

    @patch("sof_elk.management.git.GitManager.branch_cli")
    def test_branch_positional(self, mock_branch):
        """Verify 'branch <name>' works (no -b flag needed)."""
        # Simulate: sof-elk.py management branch mybranch
        args = self.parser.parse_args(["management", "branch", "mybranch"])
        args.func(args)
        mock_branch.assert_called_with("mybranch", False)

    @patch("sof_elk.management.git.GitManager.update_cli", create=True)
    def test_update_force(self, mock_update):
        """Verify 'update -f' works."""
        args = self.parser.parse_args(["management", "update", "-f"])
        args.func(args)
        mock_update.assert_called_with(True)

    @patch("sof_elk.management.elasticsearch.ElasticsearchManager.clear_cli")
    def test_clear_flags(self, mock_clear):
        """Verify 'clear -i params' works."""
        # Simulate: sof-elk.py management clear -i logstash -r
        args = self.parser.parse_args(["management", "clear", "-i", "logstash", "-r"])
        args.func(args)
        # Check that args were passed correctly
        # run_clear(args) -> clear_cli(index=..., filepath=..., nukeitall=..., reload_files=...)
        # args from parser: index="logstash", filepath=None, nukeitall=False, reload=True
        mock_clear.assert_called_with(index="logstash", filepath=None, nukeitall=False, reload_files=True)

    @patch("sof_elk.management.elasticsearch.ElasticsearchManager.list_indices")
    def test_freeze_list(self, mock_list):
        """Verify 'freeze -a list' works."""
        args = self.parser.parse_args(["management", "freeze", "-a", "list"])
        args.func(args)
        mock_list.assert_called()

    @patch("sof_elk.management.elasticsearch.ElasticsearchManager.freeze_index")
    def test_freeze_action(self, mock_freeze_idx):
        """Verify 'freeze -a freeze -i idx -t tag'."""
        args = self.parser.parse_args(["management", "freeze", "-a", "freeze", "-i", "idx", "-t", "tag"])
        args.func(args)
        # run_freeze calls freeze_index(args.index, delete_source=args.delete, newindex=args.newindex, tag=args.tag)
        mock_freeze_idx.assert_called_with("idx", delete_source=False, newindex=False, tag="tag")

