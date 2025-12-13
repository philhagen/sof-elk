import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Adjust path to the sofelk/source
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "sofelk", "source"))

from sof_elk.aws.cloudtrail import CloudTrailProcessor

class TestCloudTrailProcessor(unittest.TestCase):
    
    @patch('sof_elk.aws.common.AWSCommon.smart_open_json')
    def test_process_file_noisy(self, mock_open):
        # Setup mock data with noise
        records = {
            "Records": [
                {"eventID": "1", "requestParameters": {"bucketName": "for509trails"}},
                {"eventID": "2", "requestParameters": {"bucketName": "goodbucket"}},
                {"eventID": "3", "requestParameters": None} 
            ]
        }
        mock_open.return_value = records
        
        # Test noise reduction
        result = CloudTrailProcessor.process_file("dummy", reduce_noise=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["eventID"], "2")
        self.assertEqual(result[1]["eventID"], "3")

    @patch('sof_elk.aws.common.AWSCommon.smart_open_json')
    def test_process_file_no_noise_filtering(self, mock_open):
        records = {
            "Records": [
                {"eventID": "1", "requestParameters": {"bucketName": "for509trails"}}
            ]
        }
        mock_open.return_value = records
        result = CloudTrailProcessor.process_file("dummy", reduce_noise=False)
        self.assertEqual(len(result), 1)

    @patch('sof_elk.aws.common.AWSCommon.smart_open_json')
    def test_process_file_invalid(self, mock_open):
        mock_open.return_value = {"NotRecords": []}
        # Should print error to stderr (captured or ignored) and return empty list
        with patch('sys.stderr'):
             result = CloudTrailProcessor.process_file("dummy")
        self.assertEqual(result, [])

    def test_derive_output_file(self):
        filename = "123456789012_CloudTrail_us-east-1_20250110T0805Z_hash.json.gz"
        expected = os.path.join("processed", "123456789012", "us-east-1", "2025", "01", "cloudtrail_2025-01-10.json")
        result = CloudTrailProcessor.derive_output_file(filename, output_base="processed")
        self.assertEqual(result, expected)

    def test_derive_output_file_fallback(self):
        filename = "randomfile.json"
        with patch('sys.stderr'):
             result = CloudTrailProcessor.derive_output_file(filename, output_base="processed")
        self.assertEqual(result, os.path.join("processed", "cloudtrail_undated.json"))

    @patch('sof_elk.aws.common.AWSCommon.smart_open_json')
    def test_process_file_read_error(self, mock_open):
        mock_open.return_value = None
        result = CloudTrailProcessor.process_file("dummy")
        self.assertEqual(result, [])

    def test_remove_noise_malformed(self):
        # requestParameters is not a dict
        records = [
            {"requestParameters": "malformed_string"},
            {"requestParameters": 123}
        ]
        result = CloudTrailProcessor.remove_noise(records)
        self.assertEqual(len(result), 2)

if __name__ == '__main__':
    unittest.main()
