import unittest
from unittest.mock import MagicMock, patch
import os
from sof_elk.azure.flow import AzureFlowProcessor

class TestAzureFlow(unittest.TestCase):
    def test_create_inflight_index(self):
        ft = {
            "source_ip": "1.1.1.1",
            "destination_ip": "2.2.2.2",
            "source_port": "123",
            "destination_port": "456",
            "protocol": "6"
        }
        idx = AzureFlowProcessor.create_inflight_index(ft)
        self.assertEqual(idx, "1.1.1.1-2.2.2.2-123-456-6")

    def test_create_inflight_entry_vnet(self):
        ft = {
            "timestamp": "1000",
            "source_ip": "1.1.1.1",
            "destination_ip": "2.2.2.2",
            "source_port": "123",
            "destination_port": "456",
            "protocol": "T",
            "traffic_flow": "I",
            "flow_state": "B",
            "encryption_state": "X",
            "out_packets": "0", "out_bytes": "0", "in_packets": "0", "in_bytes": "0"
        }
        meta = {
            "flow_type": "vnet",
            "exporter_guid": "guid",
            "exporter_mac": "aabbccddeeff",
            "flow_version": 2,
            "flow_rule": "rule",
            "infile": "file",
            "state": "initial"
        }
        
        entry = AzureFlowProcessor.create_inflight_entry(ft, meta)
        self.assertEqual(entry["exporter_mac"], "aa:bb:cc:dd:ee:ff")
        self.assertEqual(entry["protocol"], "T")
        self.assertEqual(entry["encrypted"], 1)

    def test_run_no_inputs(self):
        # Just ensure it doesn't crash on invalid calls if handled
        proc = AzureFlowProcessor(infile="nonexistent", outfile="out.csv")
        with patch("sys.stderr.write"):
             res = proc.run()
        self.assertFalse(res)
