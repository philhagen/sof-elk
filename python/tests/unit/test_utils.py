import unittest
import os
import json
from sof_elk.utils.csv import CSVConverter

class TestCSVConverter(unittest.TestCase):
    def test_normalize_field_name(self):
        self.assertEqual(CSVConverter.normalize_field_name("Field Name"), "field_name")
        self.assertEqual(CSVConverter.normalize_field_name("Field (Name)"), "field_name")
        self.assertEqual(CSVConverter.normalize_field_name("  Space  "), "__space__")

    def test_convert_value(self):
        self.assertEqual(CSVConverter.convert_value("123"), 123)
        self.assertEqual(CSVConverter.convert_value("12.3"), 12.3)
        self.assertEqual(CSVConverter.convert_value("True"), True)
        self.assertEqual(CSVConverter.convert_value("false"), False)
        self.assertEqual(CSVConverter.convert_value("string"), "string")

    def test_remove_empty_fields(self):
        obj = {"a": 1, "b": "", "c": {"d": "", "e": 2}, "f": ["", 3]}
        expected = {"a": 1, "c": {"e": 2}, "f": [3]}
        self.assertEqual(CSVConverter.remove_empty_fields(obj), expected)

    def test_csv_to_json(self):
        infile = "test.csv"
        outfile = "test.json"
        with open(infile, "w") as f:
            f.write("Header One,Header Two\nValue1,123\nValue2,")
        
        CSVConverter.process_csv_to_json(infile, outfile, tags=["test"])
        
        with open(outfile, "r") as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        data = json.loads(lines[0])
        self.assertEqual(data["header_one"], "Value1")
        self.assertEqual(data["header_two"], 123)
        self.assertEqual(data["tags"], ["test"])
        
        os.remove(infile)
        os.remove(outfile)
