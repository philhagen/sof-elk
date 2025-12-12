import unittest
from unittest.mock import patch, mock_open
import sys
import os
import tempfile
import shutil

# Adjust path
# Adjust path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "sofelk", "source"))

from sof_elk.aws.common import AWSCommon
from sof_elk.aws import cli as aws_cli

class TestKickLogic(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_ensure_newline_appends(self):
        # Create a file without newline
        fpath = os.path.join(self.test_dir, "test_no_newline.json")
        with open(fpath, "wb") as f:
            f.write(b"foo")
            
        result = AWSCommon.ensure_file_ends_with_newline(fpath)
        self.assertTrue(result)
        
        with open(fpath, "rb") as f:
            content = f.read()
        self.assertEqual(content, b"foo\n")

    def test_ensure_newline_no_change(self):
        # Create a file WITH newline
        fpath = os.path.join(self.test_dir, "test_newline.json")
        with open(fpath, "wb") as f:
            f.write(b"bar\n")
            
        result = AWSCommon.ensure_file_ends_with_newline(fpath)
        self.assertFalse(result)
        
        with open(fpath, "rb") as f:
            content = f.read()
        self.assertEqual(content, b"bar\n")

    def test_ensure_newline_empty(self):
        fpath = os.path.join(self.test_dir, "empty.json")
        with open(fpath, "wb") as f:
            pass
            
        result = AWSCommon.ensure_file_ends_with_newline(fpath)
        self.assertFalse(result)

    @patch('sof_elk.aws.cli.AWSCommon.get_input_files')
    @patch('sof_elk.aws.cli.AWSCommon.ensure_file_ends_with_newline')
    @patch('sof_elk.aws.cli.os.path.exists')
    def test_kick_handler(self, mock_exists, mock_ensure, mock_get_files):
        mock_exists.return_value = True
        mock_get_files.return_value = ['file1', 'file2']
        mock_ensure.side_effect = [True, False] # First fixed, second skipped
        
        parser = aws_cli.argparse.ArgumentParser()
        aws_cli.register_subcommand(parser) # Registers 'aws' parser logic if using top level? 
        # Actually register_subcommand registers subcommands TO a parser.
        # We need to simulate the structure or just call handle_kick with mock args
        
        args = aws_cli.argparse.Namespace(target='/tmp', verbose=True)
        
        # Capture stdout
        from io import StringIO
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            aws_cli.handle_kick(args)
            output = out.getvalue()
        finally:
            sys.stdout = saved_stdout
            
        self.assertIn("Fixed: file1", output)
        self.assertIn("Scanned 2 files. Appended newline to 1 files", output)

if __name__ == '__main__':
    unittest.main()
