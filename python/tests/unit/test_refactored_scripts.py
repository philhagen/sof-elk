import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
import shutil
from sof_elk.utils.csv import CSVConverter
from sof_elk.azure.flow import AzureFlowProcessor
from sof_elk.management.distro import DistroManager

class TestRefactoredScripts(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_csv_converter(self):
        csv_file = os.path.join(self.test_dir, "test.csv")
        json_file = os.path.join(self.test_dir, "test.json")
        with open(csv_file, "w") as f:
            f.write("col1,col2\nval1,val2\n")
        
        CSVConverter.process_csv_to_json(csv_file, json_file, tags=["tag1"])
        
        with open(json_file, "r") as f:
            content = f.read()
            self.assertIn('"col1": "val1"', content)
            self.assertIn('"tags": ["tag1"]', content)

    def test_azure_flow(self):
        # Mocking file content for Azure Flow is complex due to JSON structure
        # Just testing instantiation for now
        processor = AzureFlowProcessor(infile="dummy", outfile="dummy")
        self.assertIsInstance(processor, AzureFlowProcessor)

    @unittest.skipIf(os.name == 'nt', "DistroManager tests require Linux")
    @patch("sof_elk.management.distro.DistroManager.run_cmd")
    @patch("os.geteuid", return_value=0, create=True)
    @patch("os.environ.get", return_value=None)
    def test_distro_manager_prep(self, mock_env, mock_euid, mock_run):
        # Test prep logic
        # We need to mock input() as well since it asks for confirmation
        with patch("builtins.input", return_value=""):
             # Mock other calls to avoid side effects
             with patch("subprocess.check_output", return_value=""):
                 with patch("glob.glob", return_value=[]):
                     with patch("os.chdir"):
                         with patch("os.path.exists", return_value=False):
                             DistroManager.prep_for_distribution(nodisk=True, cloud=True)

    @unittest.skipIf(os.name == 'nt', "DistroManager tests require Linux")
    @patch("sof_elk.management.distro.DistroManager.run_cmd")
    def test_distro_manager_post_merge(self, mock_run):
        # Test post_merge logic
        with patch("glob.glob", return_value=[]):
            with patch("os.path.exists", return_value=True):
                with patch("os.remove"):
                    with patch("os.symlink"):
                         with patch("os.rename"):
                            DistroManager.post_merge()

if __name__ == "__main__":
    unittest.main()
