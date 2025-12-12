import unittest
from unittest.mock import patch
import sys
import os
import subprocess

# Adjust path to the supporting-scripts
# But wrappers aren't modules, they are scripts. We can test them by running them.
# However, to avoid spawning processes in unit tests if possible (though it's robust), 
# or we can mock subprocess.call in the script if we could import it. 
# But importing scripts without .py extension or with hyphens is tricky if not using runpy.
# But they DO have .py extension.

# We will use subprocess for the wrappers as they are tiny logic. 
# But requirements said "100% code coverage within @[tests]".
# If we run subprocess, the coverage might not be captured unless we use 'coverage run'.
# To ensure the wrapper *source code* is covered by the test (as seen by coverage tool), 
# we should import the main function.

# Let's import the scripts using importlib
import importlib.util

def load_module_from_path(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

class TestWrappers(unittest.TestCase):
    
    def setUp(self):
        self.ct_wrapper_path = os.path.join(REPO_ROOT, "python", "scripts", "aws-cloudtrail2sof-elk.py")
        self.vf_wrapper_path = os.path.join(REPO_ROOT, "python", "scripts", "aws-vpcflow2sof-elk.py")

    @patch('subprocess.check_call')
    def test_cloudtrail_wrapper(self, mock_subprocess):
        # Import the module dynamically
        ct_module = load_module_from_path(self.ct_wrapper_path, "aws_cloudtrail2sofelk")
        
        # We need to mock sys.argv
        with patch.object(sys, 'argv', ['script_name', '-r', 'file.json']):
             ct_module.main()
        
        # Verify subprocess was called with correct args
        mock_subprocess.assert_called_once()
        args, kwargs = mock_subprocess.call_args
        cmd_executed = args[0]
        
        self.assertEqual(cmd_executed[1], "-m")
        self.assertEqual(cmd_executed[2], "sof_elk")
        self.assertEqual(cmd_executed[3:], ["aws", "cloudtrail", "-r", "file.json"])
        
        # Check env
        env = kwargs.get('env')
        self.assertIsNotNone(env)
        self.assertIn("PYTHONPATH", env)
        self.assertIn("sofelk", env["PYTHONPATH"])

    @patch('subprocess.check_call')
    def test_vpcflow_wrapper(self, mock_subprocess):
        # Import the module dynamically
        vf_module = load_module_from_path(self.vf_wrapper_path, "aws_vpcflow2sofelk")
        
        # We need to mock sys.argv
        with patch.object(sys, 'argv', ['script_name', '-r', 'file.json', '-w', 'out.json']):
             vf_module.main()
        
        # Verify subprocess was called with correct args
        mock_subprocess.assert_called_once()
        args, kwargs = mock_subprocess.call_args
        cmd_executed = args[0]
        
        self.assertEqual(cmd_executed[1], "-m")
        self.assertEqual(cmd_executed[2], "sof_elk")
        self.assertEqual(cmd_executed[3:], ["aws", "vpcflow", "-r", "file.json", "-w", "out.json"])
        
        env = kwargs.get('env')
        self.assertIsNotNone(env)


    @patch('subprocess.check_call')
    def test_cloudtrail_wrapper_error(self, mock_subprocess):
        ct_module = load_module_from_path(self.ct_wrapper_path, "aws_cloudtrail2sofelk_err")
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
        
        with patch.object(sys, 'argv', ['script', '-r', 'f.json']):
            with self.assertRaises(SystemExit) as cm:
                ct_module.main()
            self.assertEqual(cm.exception.code, 1)

    @patch('subprocess.check_call')
    def test_cloudtrail_wrapper_exception(self, mock_subprocess):
        ct_module = load_module_from_path(self.ct_wrapper_path, "aws_cloudtrail2sofelk_exc")
        mock_subprocess.side_effect = Exception("General failure")
        
        with patch.object(sys, 'argv', ['script', '-r', 'f.json']):
             with patch('sys.stderr') as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    ct_module.main()
                self.assertEqual(cm.exception.code, 1)

    @patch('subprocess.check_call')
    def test_vpcflow_wrapper_interrupt(self, mock_subprocess):
        vf_module = load_module_from_path(self.vf_wrapper_path, "aws_vpcflow2sofelk_int")
        mock_subprocess.side_effect = KeyboardInterrupt()
        
        with patch.object(sys, 'argv', ['script', '-r', 'f', '-w', 'o']):
            with self.assertRaises(SystemExit) as cm:
                vf_module.main()
            self.assertEqual(cm.exception.code, 130)

if __name__ == '__main__':
    unittest.main()
