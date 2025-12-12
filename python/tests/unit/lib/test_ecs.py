import unittest
import tempfile
import os
import shutil
from sof_elk.lib.ecs import ECSField, generate_csv

class TestECS(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_ecs_field_to_csv(self):
        field = ECSField(name="test.field", description="desc", field_type="keyword")
        row = field.to_csv_row()
        self.assertEqual(row['Field Name'], "test.field")
        self.assertEqual(row['Description'], "desc")
        self.assertEqual(row['Field Type'], "keyword")

    def test_generate_csv(self):
        target = os.path.join(self.test_dir, "ecs.csv")
        # We rely on existing ALL_ECS_FIELDS imported in the function
        # This is a bit of an integration test using real definitions
        res = generate_csv(target)
        self.assertTrue(res)
        self.assertTrue(os.path.exists(target))
        with open(target, "r", encoding="utf-8") as f:
            header = f.readline()
            self.assertTrue(header.startswith("Field Name,Description"))

if __name__ == '__main__':
    unittest.main()
