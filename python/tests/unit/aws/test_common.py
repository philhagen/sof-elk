import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import os
import tempfile
import shutil
import gzip
import json
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "sofelk", "source"))

from sof_elk.aws.common import AWSCommon


class TestAWSCommon(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_get_input_files_single_file(self):
        fpath = os.path.join(self.test_dir, "test.json")
        with open(fpath, "w") as f:
            f.write("{}")
        
        files = AWSCommon.get_input_files(fpath)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], fpath)

    def test_get_input_files_directory(self):
        d1 = os.path.join(self.test_dir, "d1")
        os.makedirs(d1)
        f1 = os.path.join(self.test_dir, "f1.json")
        f2 = os.path.join(d1, "f2.json")
        
        with open(f1, "w") as f: f.write("{}")
        with open(f2, "w") as f: f.write("{}")

        files = AWSCommon.get_input_files(self.test_dir)
        self.assertEqual(len(files), 2)
        self.assertTrue(f1 in files)
        self.assertTrue(f2 in files)

    def test_open_file_handle_text(self):
        fpath = os.path.join(self.test_dir, "test.txt")
        with open(fpath, "w") as f:
            f.write("content")
        
        handle = AWSCommon.open_file_handle(fpath)
        content = handle.read()
        handle.close()
        self.assertEqual(content, "content")

    def test_open_file_handle_gzip(self):
        fpath = os.path.join(self.test_dir, "test.txt.gz")
        with gzip.open(fpath, "wt") as f:
            f.write("content")
        
        handle = AWSCommon.open_file_handle(fpath)
        content = handle.read()
        handle.close()
        self.assertEqual(content, "content")

    def test_smart_open_json(self):
        fpath = os.path.join(self.test_dir, "test.json")
        data = {"key": "value"}
        with open(fpath, "w") as f:
            json.dump(data, f)
        
        loaded = AWSCommon.smart_open_json(fpath)
        self.assertEqual(loaded, data)

    def test_smart_open_json_invalid(self):
        fpath = os.path.join(self.test_dir, "bad.json")
        with open(fpath, "w") as f:
            f.write("{invalid")
        
        # Should return None and print error (captured if needed, but here just None check)
        loaded = AWSCommon.smart_open_json(fpath)
        self.assertIsNone(loaded)

    @patch('builtins.open')
    @patch('sys.stderr', new_callable=StringIO)
    def test_open_file_handle_error(self, mock_stderr, mock_open):
        mock_open.side_effect = OSError("Access denied")
        handle = AWSCommon.open_file_handle("protected.txt")
        self.assertIsNone(handle)
        self.assertIn("Error opening", mock_stderr.getvalue())

    @patch('sof_elk.aws.common.AWSCommon.open_file_handle')
    @patch('sys.stderr', new_callable=StringIO)
    def test_smart_open_json_generic_error(self, mock_stderr, mock_open_handle):
        # Mock handle context manager
        mock_handle = MagicMock()
        mock_handle.__enter__.return_value = mock_handle
        mock_handle.__exit__.return_value = None
        mock_open_handle.return_value = mock_handle
        
        # We need the context manager ENTER or the yield to raise exception?
        # The code is: with open_file_handle(...) as f:
        # If open_file_handle(...) returns mock_handle, then 'with mock_handle' calls __enter__.
        mock_handle.__enter__.side_effect = Exception("Unexpected")
        
        result = AWSCommon.smart_open_json("file.json")
        self.assertIsNone(result)
        self.assertIn("Error reading", mock_stderr.getvalue())

    @patch('builtins.open')
    @patch('sys.stderr', new_callable=StringIO)
    def test_ensure_newline_error(self, mock_stderr, mock_open):
        mock_open.side_effect = OSError("Disk failure")
        result = AWSCommon.ensure_file_ends_with_newline("disk.txt")
        self.assertFalse(result)
        self.assertIn("Error checking/updating", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
