import unittest
import os
import tempfile
import shutil
import json
import subprocess
import sys

# Paths to scripts
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CT_SCRIPT = os.path.join(PROJECT_ROOT, "python", "scripts", "aws-cloudtrail2sof-elk.py")
VPC_SCRIPT = os.path.join(PROJECT_ROOT, "python", "scripts", "aws-vpcflow2sof-elk.py")

class TestAWSScripts(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.test_dir, "source")
        self.dest_dir = os.path.join(self.test_dir, "dest")
        os.makedirs(self.source_dir)
        # os.makedirs(self.dest_dir) # Script creates it usually

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def run_script(self, cmd):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Script failed with code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        return result

    def test_cloudtrail_script_basics(self):
        # Create dummy file
        ct_file = os.path.join(self.source_dir, "123456789012_CloudTrail_us-east-1_20250101T1200Z_test.json")
        with open(ct_file, "w") as f:
            json.dump({"Records": [{"event": "test"}]}, f)

        # Run script
        cmd = [sys.executable, CT_SCRIPT, "-r", self.source_dir, "-o", self.dest_dir, "-f"]
        self.run_script(cmd)

        # Check output
        expected_out = os.path.join(self.dest_dir, "processed-logs-json", "123456789012", "us-east-1", "2025", "01", "cloudtrail_2025-01-01.json")
        if not os.path.exists(expected_out):
            print(f"Failed to find {expected_out}")
            # List dest dir
            for root, dirs, files in os.walk(self.dest_dir):
                print(f"Directory: {root}")
                for file in files:
                    print(f"  {file}")

        self.assertTrue(os.path.exists(expected_out))
        
        with open(expected_out, "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)

    def test_cloudtrail_script_noise_reduction(self):
        # Create dummy file with noise
        ct_file = os.path.join(self.source_dir, "123456789012_CloudTrail_us-east-1_20250101T1200Z_test.json")
        data = {
            "Records": [
                {"id": "1", "requestParameters": {"bucketName": "for509trails"}},
                {"id": "2", "requestParameters": {"bucketName": "valid"}}
            ]
        }
        with open(ct_file, "w") as f:
            json.dump(data, f)

        # Run script WITH reduction
        cmd = [sys.executable, CT_SCRIPT, "-r", self.source_dir, "-o", self.dest_dir, "-f", "--reduce-noise"]
        self.run_script(cmd)

        expected_out = os.path.join(self.dest_dir, "processed-logs-json", "123456789012", "us-east-1", "2025", "01", "cloudtrail_2025-01-01.json")
        self.assertTrue(os.path.exists(expected_out))
        
        with open(expected_out, "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            self.assertIn('"id": "2"', lines[0])

    def test_vpcflow_script(self):
        # Create dummy file
        vpc_file = os.path.join(self.source_dir, "vpc.json")
        with open(vpc_file, "w") as f:
            json.dump({"events": [{"message": "m1"}, {"message": "m2"}]}, f)

        outfile = os.path.join(self.test_dir, "vpc_out.log")
        
        # Run script
        cmd = [sys.executable, VPC_SCRIPT, "-r", self.source_dir, "-w", outfile]
        # It warns about non-standard output but exits 0 if success
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) # Assuming stderr isn't captured as failure by check_call unless exit code != 0

        self.assertTrue(os.path.exists(outfile))
        with open(outfile, "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0].strip(), "m1")
            self.assertEqual(lines[1].strip(), "m2")
