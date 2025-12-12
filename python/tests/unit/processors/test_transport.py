import unittest
from sof_elk.processors.transport import Transport

class TestTransport(unittest.TestCase):
    def test_tcp_flags_syn(self):
        # 0x02 -> SYN
        res = Transport.expand_tcp_flags(2)
        self.assertEqual(res['tcp_control_bits'], 2)
        self.assertIn("syn", res['tcp_flags'])

    def test_tcp_flags_ack(self):
        # 0x10 -> ACK
        res = Transport.expand_tcp_flags(16)
        self.assertIn("ack", res['tcp_flags'])

    def test_tcp_flags_combo(self):
        # 0x12 -> SYN + ACK
        res = Transport.expand_tcp_flags(18)
        self.assertIn("syn", res['tcp_flags'])
        self.assertIn("ack", res['tcp_flags'])

if __name__ == '__main__':
    unittest.main()
