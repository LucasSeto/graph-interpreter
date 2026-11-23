import csv
import io
import unittest

from data_export import build_csv, build_series_csv, build_single_series_csv


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

    def test_builds_combined_csv_with_two_series(self):
        contents = build_series_csv(
            "Experiment 1",
            "Time",
            "Temperature",
            [
                {
                    "name": "Control",
                    "points": [{"x": 0, "y": 20}, {"x": 1, "y": 21}],
                },
                {"name": "Treatment", "points": [{"x": 0, "y": 22}]},
            ],
        )
        rows = list(csv.reader(io.StringIO(contents)))

        self.assertEqual(rows[0], ["Experiment 1"])
        self.assertEqual(
            rows[1],
            [
                "Control Time",
                "Control Temperature",
                "Treatment Time",
                "Treatment Temperature",
            ],
        )
        self.assertEqual(rows[2], ["0", "20", "0", "22"])
        self.assertEqual(rows[3], ["1", "21", "", ""])

    def test_builds_individual_csv_with_only_named_axes_and_points(self):
        contents = build_single_series_csv(
            "Control",
            "Time",
            "Temperature",
            [{"x": 0, "y": 20}, {"x": 1, "y": 21}],
        )
        rows = list(csv.reader(io.StringIO(contents)))

        self.assertEqual(
            rows,
            [
                ["Control"],
                ["Time", "Temperature"],
                ["0", "20"],
                ["1", "21"],
            ],
        )
