from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pytesseract
from PIL import Image, ImageDraw
from pytesseract import Output
from pytesseract.pytesseract import TesseractNotFoundError

from calibration import Point


@dataclass(frozen=True)
class DetectedSeries:
    color: str
    hue: int
    points: tuple[Point, ...]


def _plot_mask(
    image_size: tuple[int, int],
    calibration_points: Mapping[str, Point],
) -> np.ndarray:
    width, height = image_size
    x_start = calibration_points["x_start"]
    x_end = calibration_points["x_end"]
    y_start = calibration_points["y_start"]
    y_end = calibration_points["y_end"]
    y_vector = (y_end[0] - y_start[0], y_end[1] - y_start[1])
    opposite_corner = (
        x_end[0] + y_vector[0],
        x_end[1] + y_vector[1],
    )
    upper_left = (x_start[0] + y_vector[0], x_start[1] + y_vector[1])
    polygon = [
        tuple(round(value) for value in point)
        for point in (x_start, x_end, opposite_corner, upper_left)
    ]
    mask_image = Image.new("1", image_size)
    ImageDraw.Draw(mask_image).polygon(polygon, fill=1)
    return np.asarray(mask_image, dtype=bool)


def _hue_distance(hues: np.ndarray, hue: int) -> np.ndarray:
    delta = (hues.astype(np.int16) - hue) % 256
    return np.minimum(delta, (-delta) % 256)


def _hue_peaks(hues: np.ndarray, mask: np.ndarray) -> list[int]:
    histogram = np.bincount(hues[mask], minlength=256).astype(np.int64)
    smoothed = sum(np.roll(histogram, offset) for offset in range(-4, 5))
    threshold = max(6, int(mask.sum() * 0.002))
    peak_indexes = np.flatnonzero(
        (smoothed >= np.roll(smoothed, 1))
        & (smoothed >= np.roll(smoothed, -1))
        & (smoothed >= threshold)
    )
    peak_indexes = sorted(peak_indexes, key=lambda hue: smoothed[hue], reverse=True)

    peaks: list[int] = []
    for hue in peak_indexes:
        if all(
            min((hue - existing) % 256, (existing - hue) % 256) > 10
            for existing in peaks
        ):
            peaks.append(int(hue))
        if len(peaks) == 8:
            break
    return peaks


def _scatter_centers(mask: np.ndarray) -> list[Point]:
    parents: list[int] = []
    runs: list[tuple[int, int, int, int, int]] = []
    previous_column: list[tuple[int, int, int]] = []
    previous_x: int | None = None

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(first: int, second: int) -> None:
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parents[second_root] = first_root

    for x_value in np.flatnonzero(mask.any(axis=0)):
        x = int(x_value)
        if previous_x is None or x != previous_x + 1:
            previous_column = []
        y_values = np.flatnonzero(mask[:, x])
        split_indexes = np.flatnonzero(np.diff(y_values) > 1) + 1
        for segment in np.split(y_values, split_indexes):
            y_min = int(segment[0])
            y_max = int(segment[-1])
            run_index = len(runs)
            runs.append((int(x), y_min, y_max, len(segment), int(segment.sum())))
            parents.append(run_index)
            for previous_index, previous_min, previous_max in previous_column:
                if y_min <= previous_max + 2 and y_max >= previous_min - 2:
                    union(run_index, previous_index)
        current_start = len(runs) - len(split_indexes) - 1
        previous_column = [
            (index, runs[index][1], runs[index][2])
            for index in range(current_start, len(runs))
        ]
        previous_x = x

    components: dict[int, list[tuple[int, int, int, int, int]]] = {}
    for index, run in enumerate(runs):
        components.setdefault(find(index), []).append(run)

    centers = []
    for component in components.values():
        pixel_count = sum(run[3] for run in component)
        if pixel_count < 6:
            continue
        x_center = sum(run[0] * run[3] for run in component) / pixel_count
        y_center = sum(run[4] for run in component) / pixel_count
        centers.append((x_center, y_center))
    return centers


def _continuous_line_segments(
    occupied_x: np.ndarray,
    plot_width: int,
) -> list[np.ndarray]:
    max_gap = min(20, max(4, round(plot_width * 0.05)))
    split_indexes = np.flatnonzero(np.diff(occupied_x) > max_gap + 1) + 1
    segments = np.split(occupied_x, split_indexes)
    min_span = max(24, round(plot_width * 0.06))
    return [
        segment
        for segment in segments
        if len(segment) > 1 and segment[-1] - segment[0] + 1 >= min_span
    ]


def detect_color_series(
    image: Image.Image,
    calibration_points: Mapping[str, Point],
) -> list[DetectedSeries]:
    rgb_image = image.convert("RGB")
    region = _plot_mask(rgb_image.size, calibration_points)
    hsv = np.asarray(rgb_image.convert("HSV"))
    hues = hsv[:, :, 0]
    saturated = region & (hsv[:, :, 1] >= 20) & (hsv[:, :, 2] >= 40)
    peaks = _hue_peaks(hues, saturated)
    plot_width = max(
        1,
        max(point[0] for point in calibration_points.values())
        - min(point[0] for point in calibration_points.values()),
    )
    min_pixels = max(8, round(plot_width * 0.015))
    detected: list[DetectedSeries] = []

    for hue in peaks:
        color_mask = saturated & (_hue_distance(hues, hue) <= 8)
        if int(color_mask.sum()) < min_pixels:
            continue

        occupied_x = np.flatnonzero(color_mask.any(axis=0))
        if len(occupied_x) == 0:
            continue
        line_segments = _continuous_line_segments(occupied_x, plot_width)
        if line_segments:
            points = []
            for segment in line_segments:
                segment_y = [
                    float(np.median(np.flatnonzero(color_mask[:, x])))
                    for x in segment
                ]
                for x in range(int(segment[0]), int(segment[-1]) + 1):
                    points.append(
                        (
                            float(x),
                            float(np.interp(x, segment, segment_y)),
                        )
                    )
        else:
            points = _scatter_centers(color_mask)
        if len(points) < 2:
            continue

        rgb_pixels = np.asarray(rgb_image)[color_mask]
        red, green, blue = np.mean(rgb_pixels, axis=0).round().astype(int)
        detected.append(
            DetectedSeries(
                color=f"#{red:02x}{green:02x}{blue:02x}",
                hue=hue,
                points=tuple(points),
            )
        )

    return detected


def read_legend_names(
    image: Image.Image,
    series: Sequence[DetectedSeries],
) -> tuple[dict[int, str], bool]:
    try:
        text_data = pytesseract.image_to_data(
            image.convert("RGB"),
            output_type=Output.DICT,
            config="--psm 11",
        )
    except TesseractNotFoundError:
        return {}, False

    lines: dict[tuple[int, int, int], list[tuple[str, int, int, int, int]]] = {}
    for index, text in enumerate(text_data["text"]):
        text = text.strip()
        if not text or float(text_data["conf"][index]) < 25:
            continue
        line_key = (
            int(text_data["block_num"][index]),
            int(text_data["par_num"][index]),
            int(text_data["line_num"][index]),
        )
        lines.setdefault(line_key, []).append(
            (
                text,
                int(text_data["left"][index]),
                int(text_data["top"][index]),
                int(text_data["width"][index]),
                int(text_data["height"][index]),
            )
        )

    hsv = np.asarray(image.convert("HSV"))
    names: dict[int, str] = {}
    for line in lines.values():
        name = " ".join(word[0] for word in line).strip()
        left = min(word[1] for word in line)
        top = min(word[2] for word in line)
        right = max(word[1] + word[3] for word in line)
        bottom = max(word[2] + word[4] for word in line)
        padding = max(8, (bottom - top) // 2)
        swatch_region = hsv[
            max(0, top - padding) : min(hsv.shape[0], bottom + padding),
            max(0, left - 80) : left,
        ]
        if swatch_region.size == 0:
            continue
        swatch_hues = swatch_region[:, :, 0]
        swatch_saturated = (swatch_region[:, :, 1] >= 20) & (
            swatch_region[:, :, 2] >= 40
        )
        matches = [
            int(
                (
                    swatch_saturated
                    & (_hue_distance(swatch_hues, candidate.hue) <= 8)
                ).sum()
            )
            for candidate in series
        ]
        if matches and max(matches) >= 5:
            candidate_index = int(np.argmax(matches))
            names.setdefault(candidate_index, name)
    return names, True
