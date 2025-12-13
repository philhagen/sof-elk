import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import argparse
from io import StringIO

# Adjust path finding
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "sofelk", "source"))

from sof_elk.aws import cli as aws_cli

class TestCLIExtended(unittest.TestCase):
    
    def setUp(self):
        self.parser = argparse.ArgumentParser()
        aws_cli.register_subcommand(self.parser)
    
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sys.stderr', new_callable=StringIO)
    def test_cloudtrail_outdir_not_default_error(self, mock_stderr, mock_get_files):
        # -o /tmp/custom without -f
        args = self.parser.parse_args(['cloudtrail', '-r', 'in.json', '-o', '/tmp/custom'])
        
        with self.assertRaises(SystemExit) as cm:
            args.func(args)
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("use \"-f\" to force", mock_stderr.getvalue().lower())

    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.os.path.exists')
    @patch('sys.stderr', new_callable=StringIO)
    def test_cloudtrail_outdir_exists_error(self, mock_stderr, mock_exists, mock_get_files):
        # -o /tmp/custom -f but exists and not append
        mock_exists.return_value = True
        # We need to mock os.path.expanduser or ensure /tmp/custom is treated as such
        args = self.parser.parse_args(['cloudtrail', '-r', 'in.json', '-o', '/tmp/custom', '-f'])
        
        with self.assertRaises(SystemExit) as cm:
            args.func(args)
        self.assertEqual(cm.exception.code, 3)
        self.assertIn("already exists", mock_stderr.getvalue())

    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sys.stderr', new_callable=StringIO)
    def test_cloudtrail_no_input_files(self, mock_stderr, mock_get_files):
        mock_get_files.return_value = []
        args = self.parser.parse_args(['cloudtrail', '-r', 'in.json'])
        
        with self.assertRaises(SystemExit) as cm:
            args.func(args)
        self.assertEqual(cm.exception.code, 4)

    @patch('sof_elk.aws.cli.CloudTrailProcessor')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.open')
    @patch('sof_elk.aws.cli.os.makedirs')
    @patch('sys.stdout', new_callable=StringIO)
    def test_cloudtrail_verbose(self, mock_stdout, mock_makedirs, mock_open, mock_get_files, mock_ct):
        mock_get_files.return_value = ['in.json']
        mock_ct.process_file.return_value = [{'event': 1}]
        mock_ct.derive_output_file.return_value = 'out.json'
        
        args = self.parser.parse_args(['cloudtrail', '-r', 'in.json', '-v'])
        args.func(args)
        
        out = mock_stdout.getvalue()
        self.assertIn("Found 1 files", out)
        self.assertIn("Parsing file:", out)

    @patch('sof_elk.aws.cli.CloudTrailProcessor')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.open')
    @patch('sof_elk.aws.cli.os.makedirs')
    @patch('sys.stdout', new_callable=StringIO)
    def test_cloudtrail_custom_outdir_success(self, mock_stdout, mock_makedirs, mock_open, mock_get_files, mock_ct):
        mock_get_files.return_value = ['in.json']
        mock_ct.process_file.return_value = [{'event': 1}]
        mock_ct.derive_output_file.return_value = 'out.json'
        
        # -o /tmp/custom -f
        args = self.parser.parse_args(['cloudtrail', '-r', 'in.json', '-o', '/tmp/custom', '-f'])
        args.func(args)
        
        # Check makedirs called with /tmp/custom
        mock_makedirs.assert_called()
        # Check message
        self.assertIn("Move to", mock_stdout.getvalue())

    @patch('sof_elk.aws.cli.CloudTrailProcessor')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.open')
    @patch('sof_elk.aws.cli.os.makedirs')
    def test_cloudtrail_makedirs_fail(self, mock_makedirs, mock_open, mock_get_files, mock_ct):
        mock_get_files.return_value = ['in.json']
        mock_ct.process_file.return_value = [{'event': 1}]
        mock_makedirs.side_effect = OSError("Permission denied")
        
        args = self.parser.parse_args(['cloudtrail', '-r', 'in.json'])
        # Should not crash, just pass
        args.func(args)
        mock_makedirs.assert_called()

    @patch('sof_elk.aws.cli.os.path.exists')
    @patch('sys.stderr', new_callable=StringIO)
    def test_vpcflow_output_dir_missing(self, mock_stderr, mock_exists):
        # Output directory doesn't exist
        mock_exists.return_value = False
        args = self.parser.parse_args(['vpcflow', '-r', 'in', '-w', '/bad/path/out.log'])
        
        with self.assertRaises(SystemExit) as cm:
            args.func(args)
        self.assertEqual(cm.exception.code, 8)

    @patch('sof_elk.aws.cli.os.path.exists')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sys.stderr', new_callable=StringIO)
    def test_vpcflow_no_input(self, mock_stderr, mock_get_files, mock_exists):
        mock_exists.return_value = True # Output dir exists
        mock_get_files.return_value = []
        
        args = self.parser.parse_args(['vpcflow', '-r', 'in', '-w', '/tmp/out.log'])
        with self.assertRaises(SystemExit) as cm:
            args.func(args)
        self.assertEqual(cm.exception.code, 6)

    @patch('sof_elk.aws.cli.os.path.exists')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.VPCFlowProcessor')
    @patch('sof_elk.aws.cli.open')
    @patch('sys.stdout', new_callable=StringIO)
    def test_vpcflow_verbose_and_custom_out(self, mock_stdout, mock_open, mock_vpc, mock_get_files, mock_exists):
        mock_exists.return_value = True
        mock_get_files.return_value = ['in1']
        mock_vpc.process_file.return_value = ['msg']
        
        args = self.parser.parse_args(['vpcflow', '-r', 'in', '-w', '/tmp/custom.log', '-v'])
        args.func(args)
        
        out = mock_stdout.getvalue()
        self.assertIn("Parsing file", out)
        self.assertIn("move/copy", out)

    @patch('sof_elk.aws.cli.os.path.exists')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.VPCFlowProcessor')
    @patch('sof_elk.aws.cli.open')
    @patch('sys.stdout', new_callable=StringIO)
    def test_vpcflow_no_valid_messages(self, mock_stdout, mock_open, mock_vpc, mock_get_files, mock_exists):
        mock_exists.return_value = True
        mock_get_files.return_value = ['in1']
        mock_vpc.process_file.return_value = []
        
        args = self.parser.parse_args(['vpcflow', '-r', 'in', '-w', '/tmp/out.log', '-v'])
        args.func(args)
        
        out = mock_stdout.getvalue()
        self.assertIn("No valid messages found", out)
        self.assertIn("No files were successfully converted", out)

    @patch('sof_elk.aws.cli.os.path.exists')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sys.stderr', new_callable=StringIO)
    def test_vpcflow_write_exception(self, mock_stderr, mock_get_files, mock_exists):
        mock_exists.return_value = True
        mock_get_files.return_value = ['in1']
        
        with patch('sof_elk.aws.cli.open', side_effect=IOError("Write failed")):
            args = self.parser.parse_args(['vpcflow', '-r', 'in', '-w', '/tmp/out.log'])
            with self.assertRaises(SystemExit) as cm:
                args.func(args)
            self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error writing", mock_stderr.getvalue())

    @patch('sof_elk.aws.cli.os.path.exists')
    @patch('sys.stderr', new_callable=StringIO)
    def test_kick_target_missing(self, mock_stderr, mock_exists):
        mock_exists.return_value = False
        args = self.parser.parse_args(['kick', '-t', '/missing'])
        with self.assertRaises(SystemExit) as cm:
            args.func(args)
        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
