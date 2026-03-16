"""Angle signal smoothing and gap filling"""

import logging

import numpy as np


logger = logging.getLogger(__name__)


def smooth_signal(values: list[float | None], window: int = 7) -> list[float | None]:
    if window % 2 == 0:
        window += 1

    smoothed: list[float | None] = [None] * len(values)
    start = 0

    while start < len(values):
        if values[start] is None:
            start += 1
            continue

        end = start
        while end < len(values) and values[end] is not None:
            end += 1

        segment = np.array(values[start:end], dtype=float)
        kernel = np.ones(window, dtype=float)
        sums = np.convolve(segment, kernel, mode="same")
        counts = np.convolve(np.ones(len(segment), dtype=float), kernel, mode="same")
        averaged = sums / counts

        for index, value in enumerate(averaged, start=start):
            smoothed[index] = float(value)

        start = end

    return smoothed


def fill_gaps(values: list[float | None], max_gap: int = 5) -> list[float | None]:
    filled = list(values)
    index = 0

    while index < len(filled):
        if filled[index] is not None:
            index += 1
            continue

        gap_start = index
        while index < len(filled) and filled[index] is None:
            index += 1
        gap_end = index

        gap_length = gap_end - gap_start
        left_index = gap_start - 1
        right_index = gap_end

        if (
            gap_length <= max_gap
            and left_index >= 0
            and right_index < len(filled)
            and filled[left_index] is not None
            and filled[right_index] is not None
        ):
            left_value = float(filled[left_index])
            right_value = float(filled[right_index])
            step = (right_value - left_value) / (gap_length + 1)

            for offset in range(1, gap_length + 1):
                filled[gap_start + offset - 1] = left_value + step * offset

    return filled


def extract_angle_series(frame_data: list[dict], angle_key: str) -> list[float | None]:
    series: list[float | None] = []

    for frame in frame_data:
        if not frame.get("valid_frame", False):
            series.append(None)
            continue

        value = frame.get(angle_key)
        series.append(None if value is None else float(value))

    return series


def preprocess_angles(
    frame_data: list[dict],
    angle_key: str,
    smooth_window: int = 7,
    max_gap: int = 5,
) -> list[float | None]:
    raw_series = extract_angle_series(frame_data, angle_key)
    filled_series = fill_gaps(raw_series, max_gap=max_gap)
    return smooth_signal(filled_series, window=smooth_window)
