"""Annotated video generation"""

import logging
import subprocess
from pathlib import Path
from typing import Any

import cv2
import imageio_ffmpeg
import mediapipe as mp


logger = logging.getLogger(__name__)


def convert_to_mp4(avi_path: str, mp4_path: str) -> None:
    avi_file = Path(avi_path)
    if not avi_file.exists():
        return

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(avi_file),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(mp4_path),
    ]

    completed = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    logger.debug("ffmpeg stdout: %s", completed.stdout)
    avi_file.unlink(missing_ok=True)


def _get_completed_reps(frame_index: int, rep_windows: list[dict]) -> int:
    """Returns how many reps have been fully completed at or before this frame."""
    return sum(1 for rep in rep_windows if rep["end_frame"] <= frame_index)


def _is_mid_rep(frame_index: int, rep_windows: list[dict]) -> bool:
    """Returns True if the current frame falls inside an active rep window."""
    return any(
        rep["start_frame"] <= frame_index <= rep["end_frame"]
        for rep in rep_windows
    )


def annotate_video(
    input_path: str,
    output_path: str,
    frame_data: list[dict],
    rep_windows: list[dict],
    raw_landmarks: list[Any],
) -> str:
    logger.info("Starting video annotation for %s", input_path)

    input_video = Path(input_path)
    output_video = Path(output_path)
    output_video.parent.mkdir(parents=True, exist_ok=True)
    avi_path = output_video.with_suffix(".avi")

    cap = cv2.VideoCapture(str(input_video))
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open input video: {input_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    writer = cv2.VideoWriter(
        str(avi_path),
        cv2.VideoWriter_fourcc(*"XVID"),
        fps if fps > 0 else 30.0,
        (width, height),
    )

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    frame_index = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_info = frame_data[frame_index] if frame_index < len(frame_data) else {}
        landmarks = raw_landmarks[frame_index] if frame_index < len(raw_landmarks) else None
        valid_frame = bool(frame_info.get("valid_frame", False))
        knee_angle = frame_info.get("knee_angle")
        hip_angle = frame_info.get("hip_angle")

        completed_reps = _get_completed_reps(frame_index, rep_windows)
        in_rep = _is_mid_rep(frame_index, rep_windows)
        display_count = completed_reps + 1 if in_rep else completed_reps

        if landmarks is not None:
            mp_drawing.draw_landmarks(frame, landmarks, mp_pose.POSE_CONNECTIONS)

        if valid_frame:
            if knee_angle is not None:
                cv2.putText(
                    frame,
                    f"Knee: {int(knee_angle)} deg",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
            if hip_angle is not None:
                cv2.putText(
                    frame,
                    f"Hip: {int(hip_angle)} deg",
                    (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

        cv2.putText(
            frame,
            f"Rep: {display_count}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        if in_rep:
            cv2.rectangle(frame, (5, 5), (width - 5, height - 5), (0, 255, 255), 4)

        status_text = "DOWN" if knee_angle is not None and knee_angle < 110 else "UP"
        cv2.putText(
            frame,
            f"Status: {status_text}",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255) if status_text == "DOWN" else (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        writer.write(frame)
        frame_index += 1

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    convert_to_mp4(str(avi_path), str(output_video))

    logger.info("Annotated %s frames", frame_index)
    logger.info("Annotated video output: %s", output_video)
    return str(output_video)