import unittest

from calibration import (
    AxisCalibration,
    default_calibration_points,
    pixel_to_data,
)


class PixelToDataTests(unittest.TestCase):
    def test_default_references_start_near_axis_ends(self):
        points = default_calibration_points(1000, 800)

        self.assertEqual(points["x_start"], (50, 759))
        self.assertEqual(points["x_end"], (949, 759))
        self.assertEqual(points["y_start"], points["x_start"])
        self.assertEqual(points["y_end"], (50, 40))

    def test_default_references_span_small_images(self):
        points = default_calibration_points(2, 2)

        self.assertEqual(points["x_start"], (0, 1))
        self.assertEqual(points["x_end"], (1, 1))
        self.assertEqual(points["y_end"], (0, 0))

    def test_converts_points_from_non_origin_axis_references(self):
        x, y = pixel_to_data(
            x_axis=AxisCalibration((100, 220), 2, (300, 220), 10),
            y_axis=AxisCalibration((50, 200), 1, (50, 100), 6),
            pixel=(150, 160),
        )

        self.assertAlmostEqual(x, 4)
        self.assertAlmostEqual(y, 3)

    def test_converts_skewed_axis_references(self):
        x, y = pixel_to_data(
            x_axis=AxisCalibration((40, 40), 2, (80, 60), 6),
            y_axis=AxisCalibration((29, 6), 3, (44, -34), 8),
            pixel=(75, 10),
        )

        self.assertAlmostEqual(x, 4)
        self.assertAlmostEqual(y, 5)

    def test_keeps_axis_calibrations_independent(self):
        x, y = pixel_to_data(
            x_axis=AxisCalibration((100, 200), 150, (350, 200), 400),
            y_axis=AxisCalibration((25, 210), 1, (25, 110), 6),
            pixel=(150, 160),
        )

        self.assertAlmostEqual(x, 200)
        self.assertAlmostEqual(y, 3.5)

    def test_changing_a_reference_value_recalculates_a_point(self):
        y_axis = AxisCalibration((50, 200), 1, (50, 100), 6)
        pixel = (150, 200)

        original_x, _ = pixel_to_data(
            AxisCalibration((100, 200), 150, (350, 200), 400),
            y_axis,
            pixel,
        )
        updated_x, _ = pixel_to_data(
            AxisCalibration((100, 200), 150, (350, 200), 500),
            y_axis,
            pixel,
        )

        self.assertAlmostEqual(original_x, 200)
        self.assertAlmostEqual(updated_x, 220)

    def test_moving_a_reference_pixel_recalculates_a_point(self):
        x_axis = AxisCalibration((100, 200), 150, (350, 200), 400)
        y_axis = AxisCalibration((50, 200), 1, (50, 100), 6)
        pixel = (150, 160)

        original_x, original_y = pixel_to_data(x_axis, y_axis, pixel)
        updated_x, updated_y = pixel_to_data(
            AxisCalibration((120, 200), 150, (350, 200), 400),
            y_axis,
            pixel,
        )

        self.assertAlmostEqual(original_x, 200)
        self.assertAlmostEqual(updated_x, 150 + 30 * 250 / 230)
        self.assertAlmostEqual(original_y, updated_y)

    def test_rejects_duplicate_values_on_an_axis(self):
        x_axis = AxisCalibration((0, 0), 1, (1, 0), 1)
        y_axis = AxisCalibration((0, 0), 0, (0, 1), 1)

        with self.assertRaisesRegex(ValueError, "must be different"):
            pixel_to_data(x_axis, y_axis, (0, 0))

    def test_rejects_parallel_axis_references(self):
        x_axis = AxisCalibration((0, 0), 0, (3, 6), 3.3)
        y_axis = AxisCalibration((0, 1), 0, (2, 5), 2.2)

        with self.assertRaisesRegex(ValueError, "must not be parallel"):
            pixel_to_data(x_axis, y_axis, (0, 0))
