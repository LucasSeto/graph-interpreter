import csv
import io
import unittest

from data_export import build_csv


class BuildCsvTests(unittest.TestCase):
    def test_includes_dataset_name_then_labeled_columns(self):
        contents = build_csv(
            "Monthly sales",
            ["Point", "Month", "Revenue ($)", "Pixel X", "Pixel Y"],
            [
                {
                    "Point": 1,
                    "Month": 2,
                    "Revenue ($)": 150.5,
                    "Pixel X": 80,
                    "Pixel Y": 120,
                }
            ],
        )
        rows = list(csv.reader(io.StringIO(contents)))

        self.assertEqual(rows[0], ["Monthly sales"])
        self.assertEqual(
            rows[1], ["Point", "Month", "Revenue ($)", "Pixel X", "Pixel Y"]
        )
        self.assertEqual(rows[2], ["1", "2", "150.5", "80", "120"])
