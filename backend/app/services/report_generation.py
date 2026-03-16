"""CSV and plot artifact generation"""

import csv
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def generate_csv(frame_data: list[dict], output_path: str) -> str:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "frame_index",
                "timestamp_seconds",
                "knee_angle",
                "hip_angle",
                "landmark_confidence",
                "valid_frame",
            ]
        )

        for frame in frame_data:
            writer.writerow(
                [
                    frame.get("frame_index"),
                    frame.get("timestamp_seconds"),
                    frame.get("knee_angle"),
                    frame.get("hip_angle"),
                    frame.get("landmark_confidence"),
                    frame.get("valid_frame"),
                ]
            )

    logger.info("Generated CSV report at %s", output_file)
    return output_path


def generate_plot(frame_data: list[dict], rep_windows: list[dict], output_path: str) -> str:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    valid_frames = [frame for frame in frame_data if frame.get("valid_frame")]
    frame_indices = [frame["frame_index"] for frame in valid_frames]
    knee_angles = [frame["knee_angle"] for frame in valid_frames]
    hip_angles = [frame["hip_angle"] for frame in valid_frames]

    plt.figure(figsize=(12, 6))
    plt.plot(frame_indices, knee_angles, color="blue", label="Knee Angle")
    plt.plot(frame_indices, hip_angles, color="orange", label="Hip Angle")

    for rep_window in rep_windows:
        start_frame = rep_window["start_frame"]
        end_frame = rep_window["end_frame"]
        mid_frame = (start_frame + end_frame) / 2
        plt.axvspan(start_frame, end_frame, color="lightblue", alpha=0.2)
        plt.text(mid_frame, 180, f"Rep {rep_window['rep_index']}", ha="center", va="top")

    plt.axhline(100, color="red", linestyle="--", label="Depth Threshold")
    plt.axhline(155, color="green", linestyle="--", label="Standing Threshold")
    plt.title("Knee and Hip Angles Over Time")
    plt.xlabel("Frame Index")
    plt.ylabel("Angle (degrees)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    logger.info("Generated angle plot at %s", output_file)
    return output_path
