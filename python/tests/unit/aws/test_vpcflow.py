import unittest
from unittest.mock import MagicMock, patch
from sof_elk.aws.vpcflow import VPCFlowProcessor

class TestVPCFlowProcessor(unittest.TestCase):

    @patch("sof_elk.aws.common.AWSCommon.smart_open_json")
    def test_process_file_valid(self, mock_json):
        mock_json.return_value = {
            "events": [
                {"message": "log_entry_1"},
                {"message": "log_entry_2"},
                {"other": "ignore"}
            ]
        }
        messages = VPCFlowProcessor.process_file("dummy.json")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], "log_entry_1")
        self.assertEqual(messages[1], "log_entry_2")

    @patch("sof_elk.aws.common.AWSCommon.smart_open_json")
    def test_process_file_wrong_structure(self, mock_json):
        mock_json.return_value = {"not_events": []}
        messages = VPCFlowProcessor.process_file("dummy.json")
        self.assertEqual(messages, [])

    @patch("sof_elk.aws.common.AWSCommon.smart_open_json")
    def test_process_file_read_fail(self, mock_json):
        mock_json.return_value = None
        messages = VPCFlowProcessor.process_file("dummy.json")
        self.assertEqual(messages, [])
