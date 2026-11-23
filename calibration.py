from dataclasses import dataclass
import math
from typing import Tuple


Point = Tuple[float, float]


def default_calibration_points(width: int, height: int) -> dict[str, Point]:
    left_x = round((width - 1) * 0.05)
    right_x = round((width - 1) * 0.95)
    top_y = round((height - 1) * 0.05)
    bottom_y = round((height - 1) * 0.95)
    if width > 1 and left_x == right_x:
        left_x, right_x = 0, width - 1
    if height > 1 and top_y == bottom_y:
        top_y, bottom_y = 0, height - 1

    return {
        "x_start": (left_x, bottom_y),
        "x_end": (right_x, bottom_y),
        "y_start": (left_x, bottom_y),
        "y_end": (left_x, top_y),
    }


@dataclass(frozen=True)
class AxisCalibration:
    pixel_start: Point
    value_start: float
    pixel_end: Point
    value_end: float
    scale: str = "linear"

    def pixel_span(self) -> Point:
        return (
            self.pixel_end[0] - self.pixel_start[0],
            self.pixel_end[1] - self.pixel_start[1],
        )

    def value_span(self) -> float:
        if self.scale not in ("linear", "logarithmic"):
            raise ValueError("axis scale must be linear or logarithmic")
        if self.scale == "logarithmic":
            if self.value_start <= 0 or self.value_end <= 0:
                raise ValueError(
                    "logarithmic axes require both known values to be greater than zero"
                )
            start = math.log(self.value_start)
            end = math.log(self.value_end)
        else:
            start = self.value_start
            end = self.value_end
        span = end - start
        if span == 0:
            raise ValueError("the two known values on each axis must be different")
        return span

    def pixel_origin(self, pixel_span: Point, value_span: float) -> Point:
        value_start = (
            math.log(self.value_start)
            if self.scale == "logarithmic"
            else self.value_start
        )
        return (
            self.pixel_start[0] - pixel_span[0] * value_start / value_span,
            self.pixel_start[1] - pixel_span[1] * value_start / value_span,
        )

    def inverse_value(self, value: float) -> float:
        return math.exp(value) if self.scale == "logarithmic" else value


def pixel_to_data(
    x_axis: AxisCalibration,
    y_axis: AxisCalibration,
    pixel: Point,
) -> Point:
    x_pixel_span = x_axis.pixel_span()
    y_pixel_span = y_axis.pixel_span()
    x_value_span = x_axis.value_span()
    y_value_span = y_axis.value_span()
    pixel_determinant = (
        x_pixel_span[0] * y_pixel_span[1]
        - y_pixel_span[0] * x_pixel_span[1]
    )
    if pixel_determinant == 0:
        raise ValueError("the x- and y-axis reference directions must not be parallel")

    x_origin = x_axis.pixel_origin(x_pixel_span, x_value_span)
    y_origin = y_axis.pixel_origin(y_pixel_span, y_value_span)
    x_delta = (pixel[0] - x_origin[0], pixel[1] - x_origin[1])
    y_delta = (pixel[0] - y_origin[0], pixel[1] - y_origin[1])

    x_coordinate = (
        (x_delta[0] * y_pixel_span[1] - y_pixel_span[0] * x_delta[1])
        * x_value_span
        / pixel_determinant
    )
    y_coordinate = (
        (x_pixel_span[0] * y_delta[1] - y_delta[0] * x_pixel_span[1])
        * y_value_span
        / pixel_determinant
    )
    return (
        x_axis.inverse_value(x_coordinate),
        y_axis.inverse_value(y_coordinate),
    )
