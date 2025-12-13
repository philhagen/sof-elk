import unittest
from sof_elk.processors.ntfs import NTFS

class TestNTFS(unittest.TestCase):
    def test_parse_read_only(self):
        # 1 -> ReadOnly
        res = NTFS.parse_file_attributes(1)
        self.assertTrue(res['readonly'])
        self.assertFalse(res['hidden'])

    def test_parse_hidden(self):
        # 2 -> Hidden
        res = NTFS.parse_file_attributes(2)
        self.assertTrue(res['hidden'])
        self.assertFalse(res['readonly'])

    def test_parse_combo(self):
        # 3 -> ReadOnly + Hidden
        res = NTFS.parse_file_attributes(3)
        self.assertTrue(res['readonly'])
        self.assertTrue(res['hidden'])

if __name__ == '__main__':
    unittest.main()
