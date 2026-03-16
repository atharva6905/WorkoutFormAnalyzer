"""Rep segmentation from smoothed angle signals"""

import logging


logger = logging.getLogger(__name__)


def detect_reps(
    knee_angles: list[float | None],
    fps: float,
    min_depth_angle: float = 100.0,
    top_angle: float = 155.0,
    min_rep_frames: int = 15,
    min_amplitude: float = 40.0,
) -> list[dict]:
    rep_windows: list[dict] = []
    in_cycle = False
    last_top_index: int | None = None
    last_top_value: float | None = None
    start_frame: int | None = None
    min_knee_angle: float | None = None
    max_knee_angle: float | None = None

    for frame_index, angle in enumerate(knee_angles):
        if angle is None:
            continue

        if not in_cycle:
            if angle >= top_angle:
                last_top_index = frame_index
                last_top_value = angle

            if angle < min_depth_angle:
                in_cycle = True
                start_frame = last_top_index if last_top_index is not None else frame_index
                min_knee_angle = angle
                max_knee_angle = max(last_top_value, angle) if last_top_value is not None else angle
            continue

        min_knee_angle = angle if min_knee_angle is None else min(min_knee_angle, angle)
        max_knee_angle = angle if max_knee_angle is None else max(max_knee_angle, angle)

        if angle > top_angle and start_frame is not None and min_knee_angle is not None and max_knee_angle is not None:
            end_frame = frame_index
            frame_span = end_frame - start_frame + 1
            amplitude = max_knee_angle - min_knee_angle

            if frame_span >= min_rep_frames and amplitude >= min_amplitude:
                rep_windows.append(
                    {
                        "rep_index": len(rep_windows) + 1,
                        "start_frame": start_frame,
                        "end_frame": end_frame,
                        "min_knee_angle": float(min_knee_angle),
                        "depth_reached": min_knee_angle < min_depth_angle,
                    }
                )

            in_cycle = False
            last_top_index = frame_index
            last_top_value = angle
            start_frame = None
            min_knee_angle = None
            max_knee_angle = None

    logger.info("Detected %s reps", len(rep_windows))
    return rep_windows


def extract_rep_metrics(
    rep_windows: list[dict],
    knee_angles: list[float | None],
    hip_angles: list[float | None],
    frame_data: list[dict],
) -> list[dict]:
    rep_metrics: list[dict] = []

    for rep_window in rep_windows:
        start_frame = rep_window["start_frame"]
        end_frame = rep_window["end_frame"]

        knee_window = [value for value in knee_angles[start_frame : end_frame + 1] if value is not None]
        hip_window = [value for value in hip_angles[start_frame : end_frame + 1] if value is not None]
        confidence_values = [
            float(frame.get("landmark_confidence", 0.0))
            for frame in frame_data[start_frame : end_frame + 1]
            if frame.get("landmark_confidence") is not None
        ]

        min_knee_angle = min(knee_window) if knee_window else None
        max_knee_angle = max(knee_window) if knee_window else None
        min_hip_angle = min(hip_window) if hip_window else None
        max_hip_angle = max(hip_window) if hip_window else None
        confidence_score = (
            sum(confidence_values) / len(confidence_values) if confidence_values else None
        )
        notes = "Shallow depth" if min_knee_angle is not None and min_knee_angle > 110 else None

        rep_metrics.append(
            {
                "rep_index": rep_window["rep_index"],
                "start_frame": start_frame,
                "end_frame": end_frame,
                "min_knee_angle": min_knee_angle,
                "max_knee_angle": max_knee_angle,
                "min_hip_angle": min_hip_angle,
                "max_hip_angle": max_hip_angle,
                "confidence_score": confidence_score,
                "notes": notes,
            }
        )

    return rep_metrics
