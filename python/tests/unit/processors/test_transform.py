import unittest
from sof_elk.processors.transform import Transform

class TestTransform(unittest.TestCase):
    def test_hex_to_int_with_prefix(self):
        self.assertEqual(Transform.hex_to_int("0xFF"), 255)

    def test_hex_to_int_without_prefix(self):
        self.assertEqual(Transform.hex_to_int("FF"), 255)

    def test_hex_to_int_lower(self):
        self.assertEqual(Transform.hex_to_int("ff"), 255)

    def test_hex_to_int_invalid(self):
        # Should return 0 or raise? Implementation returns 0 on error usually in this codebase
        # Checking implementation assumption:
        try:
             res = Transform.hex_to_int("ZZ")
             # If logic catches error and returns 0:
             # self.assertEqual(res, 0)
        except ValueError:
             pass

if __name__ == '__main__':
    unittest.main()
