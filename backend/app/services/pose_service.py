"""Pose landmark extraction using MediaPipe."""

import logging
import math
import os
from typing import Any

import cv2
import mediapipe as mp


os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

logger = logging.getLogger(__name__)


def calculate_angle(a, b, c):
    """Calculate the angle (in degrees) formed by three points (a-b-c)."""
    ax, ay = a[0] - b[0], a[1] - b[1]
    cx, cy = c[0] - b[0], c[1] - b[1]
    dot = ax * cx + ay * cy
    mag_a = math.sqrt(ax * ax + ay * ay)
    mag_c = math.sqrt(cx * cx + cy * cy)
    denom = mag_a * mag_c
    if denom < 1e-6:
        return None
    cos_val = max(-1.0, min(1.0, dot / denom))
    return math.degrees(math.acos(cos_val))


def get_landmark_coords(landmarks, idx, width, height):
    """Convert MediaPipe landmark (normalized x, y) to pixel coordinates."""
    lm = landmarks[idx]
    return (int(lm.x * width), int(lm.y * height)), lm.visibility


def good(vis, thr=0.5):
    """Check if a landmark's visibility is good enough."""
    return vis is not None and vis >= thr


def get_video_metadata(video_path: str) -> dict[str, float | int]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"fps": 0.0, "width": 0, "height": 0, "total_frames": 0}

    metadata = {
        "fps": float(cap.get(cv2.CAP_PROP_FPS) or 0.0),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0),
    }
    cap.release()
    return metadata


def _get_side_landmarks(lms, width: int, height: int, mp_pose):
    left_points = [
        get_landmark_coords(lms, mp_pose.PoseLandmark.LEFT_HIP, width, height),
        get_landmark_coords(lms, mp_pose.PoseLandmark.LEFT_KNEE, width, height),
        get_landmark_coords(lms, mp_pose.PoseLandmark.LEFT_ANKLE, width, height),
        get_landmark_coords(lms, mp_pose.PoseLandmark.LEFT_SHOULDER, width, height),
    ]
    left_visibilities = [visibility for _, visibility in left_points]
    if all(good(visibility) for visibility in left_visibilities):
        return left_points

    right_points = [
        get_landmark_coords(lms, mp_pose.PoseLandmark.RIGHT_HIP, width, height),
        get_landmark_coords(lms, mp_pose.PoseLandmark.RIGHT_KNEE, width, height),
        get_landmark_coords(lms, mp_pose.PoseLandmark.RIGHT_ANKLE, width, height),
        get_landmark_coords(lms, mp_pose.PoseLandmark.RIGHT_SHOULDER, width, height),
    ]
    return right_points


def extract_landmarks(video_path: str) -> tuple[list[dict[str, int | float | bool | None]], list[Any]]:
    logger.info("Starting landmark extraction for %s", video_path)

    metadata = get_video_metadata(video_path)
    fps = metadata["fps"]
    width = metadata["width"]
    height = metadata["height"]

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.info("Processed 0 frames with 0 valid frames")
        return [], []

    mp_pose = mp.solutions.pose
    frame_data: list[dict[str, int | float | bool | None]] = []
    raw_landmarks: list[Any] = []
    valid_frame_count = 0
    total_frames_processed = 0

    with mp_pose.Pose(model_complexity=1, enable_segmentation=False) as pose:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)
            raw_landmarks.append(results.pose_landmarks)

            knee_angle = None
            hip_angle = None
            landmark_confidence = 0.0
            valid_frame = False

            if results.pose_landmarks:
                lms = results.pose_landmarks.landmark
                side_points = _get_side_landmarks(lms, width, height, mp_pose)
                (hip, hip_vis), (knee, knee_vis), (ankle, ankle_vis), (shoulder, shoulder_vis) = side_points
                visibilities = [hip_vis, knee_vis, ankle_vis, shoulder_vis]
                landmark_confidence = sum(visibilities) / len(visibilities)
                valid_frame = all(good(visibility) for visibility in visibilities)

                knee_angle = calculate_angle(hip, knee, ankle)
                hip_angle = calculate_angle(shoulder, hip, knee)

            if valid_frame:
                valid_frame_count += 1

            timestamp_seconds = (total_frames_processed / fps) if fps else 0.0
            frame_data.append(
                {
                    "frame_index": total_frames_processed,
                    "timestamp_seconds": timestamp_seconds,
                    "knee_angle": knee_angle,
                    "hip_angle": hip_angle,
                    "landmark_confidence": landmark_confidence,
                    "valid_frame": valid_frame,
                }
            )
            total_frames_processed += 1

    cap.release()

    logger.info("Processed %s frames during landmark extraction", total_frames_processed)
    logger.info("Valid frame count during landmark extraction: %s", valid_frame_count)
    return frame_data, raw_landmarks
