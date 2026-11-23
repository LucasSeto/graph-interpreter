import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw
from pytesseract.pytesseract import TesseractNotFoundError

from series_detection import DetectedSeries, detect_color_series, read_legend_names


class DetectColorSeriesTests(unittest.TestCase):
    def setUp(self):
        self.calibration_points = {
            "x_start": (20, 120),
            "x_end": (180, 120),
            "y_start": (20, 120),
            "y_end": (20, 20),
        }

    def test_detects_two_distinct_colored_lines(self):
        image = Image.new("RGB", (200, 140), "white")
        draw = ImageDraw.Draw(image)
        draw.line((30, 55, 170, 55), fill="red", width=2)
        draw.line((30, 90, 170, 90), fill="blue", width=2)

        series = detect_color_series(image, self.calibration_points)

        self.assertEqual(len(series), 2)
        self.assertTrue(all(len(item.points) > 100 for item in series))
        self.assertEqual(
            {item.points[0][1] for item in series},
            {55.5, 90.5},
        )

    def test_tracks_a_short_low_saturation_dashed_line_along_its_length(self):
        image = Image.new("RGB", (200, 140), "white")
        draw = ImageDraw.Draw(image)
        draw.line((30, 55, 170, 55), fill="red", width=2)
        for x in range(65, 116, 18):
            draw.line((x, 90, min(x + 14, 115), 90), fill="#eaf3ff", width=2)

        series = detect_color_series(image, self.calibration_points)

        self.assertEqual(len(series), 2)
        self.assertEqual(
            sorted(len(item.points) for item in series),
            [51, 141],
        )

    def test_detects_scatter_markers_as_individual_points(self):
        image = Image.new("RGB", (200, 140), "white")
        draw = ImageDraw.Draw(image)
        for x, y in ((50, 50), (100, 70), (150, 95)):
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="green")

        series = detect_color_series(image, self.calibration_points)

        self.assertEqual(len(series), 1)
        self.assertEqual(len(series[0].points), 3)
        self.assertEqual(
            {(round(x), round(y)) for x, y in series[0].points},
            {(50, 50), (100, 70), (150, 95)},
        )

    def test_separates_red_and_orange_lines(self):
        image = Image.new("RGB", (200, 140), "white")
        draw = ImageDraw.Draw(image)
        draw.line((30, 55, 170, 55), fill="red", width=2)
        draw.line((30, 90, 170, 90), fill="#ff8000", width=2)

        series = detect_color_series(image, self.calibration_points)

        self.assertEqual(len(series), 2)

    def test_ignores_grayscale_content(self):
        image = Image.new("RGB", (200, 140), "white")
        ImageDraw.Draw(image).line((30, 60, 170, 60), fill="#555555", width=2)

        self.assertEqual(
            detect_color_series(image, self.calibration_points),
            [],
        )

    def test_reads_a_legend_name_from_a_matching_color_swatch(self):
        image = Image.new("RGB", (160, 50), "white")
        ImageDraw.Draw(image).line((40, 25, 55, 25), fill="red", width=3)
        ocr_words = {
            "text": ["Control"],
            "conf": ["90.5"],
            "block_num": [1],
            "par_num": [1],
            "line_num": [1],
            "left": [65],
            "top": [18],
            "width": [50],
            "height": [15],
        }
        series = [DetectedSeries("#ff0000", 0, ((45, 25), (50, 25)))]

        with patch(
            "series_detection.pytesseract.image_to_data",
            return_value=ocr_words,
        ):
            names, available = read_legend_names(image, series)

        self.assertTrue(available)
        self.assertEqual(names, {0: "Control"})

    def test_allows_manual_names_when_tesseract_is_not_installed(self):
        image = Image.new("RGB", (160, 50), "white")
        series = [DetectedSeries("#ff0000", 0, ((45, 25), (50, 25)))]

        with patch(
            "series_detection.pytesseract.image_to_data",
            side_effect=TesseractNotFoundError(),
        ):
            names, available = read_legend_names(image, series)

        self.assertFalse(available)
        self.assertEqual(names, {})
