import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import argparse

# Adjust path to find the sofelk module
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "sofelk", "source"))

from sof_elk.aws import cli as aws_cli

class TestAWSCLI(unittest.TestCase):
    
    def setUp(self):
        self.parser = argparse.ArgumentParser()
        aws_cli.register_subcommand(self.parser)

    @patch('sof_elk.aws.cli.CloudTrailProcessor')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.open')
    @patch('sof_elk.aws.cli.os.makedirs')
    @patch('sof_elk.aws.cli.os.path.exists')
    def test_cloudtrail_command_basic(self, mock_exists, mock_makedirs, mock_open, mock_get_files, mock_ct_proc):
        # Setup mocks
        mock_get_files.return_value = ['/tmp/test_ct.json']
        mock_ct_proc.process_file.return_value = [{'event': 'test'}]
        mock_ct_proc.derive_output_file.return_value = 'processed/out.json'
        mock_exists.return_value = False # Directory doesn't exist, trigger makedirs

        args = self.parser.parse_args(['cloudtrail', '-r', '/tmp/test_ct.json'])
        
        # Execute handler
        args.func(args)

        # Assertions
        mock_get_files.assert_called_once_with('/tmp/test_ct.json')
        mock_ct_proc.process_file.assert_called_once()
        mock_makedirs.assert_called()
        mock_open.assert_called()

    @patch('sof_elk.aws.cli.VPCFlowProcessor')
    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.open')
    @patch('sof_elk.aws.cli.os.path.exists')
    def test_vpcflow_command_basic(self, mock_exists, mock_open, mock_get_files, mock_vpc_proc):
        # Setup mocks
        mock_get_files.return_value = ['/tmp/test_vpc.json']
        mock_vpc_proc.process_file.return_value = ['msg1', 'msg2']
        mock_exists.return_value = True # Parent dir exists

        # Target output file needs to be safe for logic check
        # Logic checks if parent startswith DEFAULT_DESTDIR_NFARCH
        target_file = os.path.join(aws_cli.DEFAULT_DESTDIR_NFARCH, 'out.log')
        
        args = self.parser.parse_args(['vpcflow', '-r', '/tmp/test_vpc.json', '-w', target_file])
        
        # Execute handler
        args.func(args)
        
        # Assertions
        mock_get_files.assert_called_once_with('/tmp/test_vpc.json')
        mock_vpc_proc.process_file.assert_called_once()
        mock_open.assert_called()

if __name__ == '__main__':
    unittest.main()
