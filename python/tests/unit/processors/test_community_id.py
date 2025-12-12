import unittest
from sof_elk.processors.community_id import CommunityID

class TestCommunityID(unittest.TestCase):
    def test_compute_tcp(self):
        # 128.232.110.120:34855 -> 66.35.250.204:80 (TCP)
        cid = CommunityID.compute("128.232.110.120", "66.35.250.204", 34855, 80, 6)
        self.assertEqual(cid, "1:LQU9qZlK+B5F3KDmev6m5PMibrg=")

    def test_compute_udp(self):
        # Verify UDP works same/correctly
        cid = CommunityID.compute("127.0.0.1", "127.0.0.1", 123, 123, 17)
        self.assertTrue(cid.startswith("1:"))

if __name__ == '__main__':
    unittest.main()
