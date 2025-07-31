"""
pose_video.py - Updated for MP4 Output
- Uses lowest-point logic for depth feedback (no flicker).
- Modularized analyze_squat(video_path).
- Outputs: annotated MP4 video, angles CSV, knee angle plot.
- Converts AVI → MP4 (H.264) for browser compatibility.
"""

import cv2
import mediapipe as mp
import math
import csv
import matplotlib.pyplot as plt
import os
from pathlib import Path
import imageio.v3 as iio
import subprocess
import imageio_ffmpeg


# Suppress TensorFlow/MediaPipe warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# ---------- Config ----------
KNEE_BOTTOM = 100    # Bottom threshold for detecting down phase
KNEE_TOP = 160       # Top threshold for detecting up phase
DEPTH_THRESHOLD = 110  # If min knee angle > this, feedback "Go deeper!"


# ---------- Utilities ----------

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


def save_csv(log_data, filename='outputs/angles_log.csv'):
    """Save angle and feedback data to CSV."""
    os.makedirs('outputs', exist_ok=True)
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Frame', 'Time (s)', 'Knee Angle (deg)', 'Hip Angle (deg)', 'Feedback'])
        writer.writerows(log_data)
    print(f"[INFO] Angle data saved to '{filename}'.")


def plot_knee_angles(log_data, filename='outputs/knee_angle_plot.png'):
    """Plot knee angles over time and save as an image."""
    frames = [row[0] for row in log_data]
    knee_angles = [row[2] for row in log_data]

    plt.figure(figsize=(10, 5))
    plt.plot(frames, knee_angles, label='Knee Angle', color='blue')
    plt.axhline(KNEE_BOTTOM, color='red', linestyle='--', label='Bottom Threshold')
    plt.axhline(KNEE_TOP, color='green', linestyle='--', label='Top Threshold')
    plt.xlabel('Frame')
    plt.ylabel('Knee Angle (deg)')
    plt.title('Knee Angle Over Time')
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"[INFO] Knee angle plot saved to '{filename}'.")


def convert_to_mp4(avi_path='outputs/pose_output_video.avi',
                   mp4_path='outputs/pose_output_video.mp4'):
    """Convert AVI to MP4 (H.264) using ffmpeg (much more robust than imageio)."""
    avi_file = Path(avi_path)
    if not avi_file.exists():
        print(f"[WARN] AVI not found, skipping conversion: {avi_path}")
        return

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()  # bundled ffmpeg path
    cmd = [
        ffmpeg_exe,
        "-y",                    # overwrite
        "-i", str(avi_file),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(mp4_path)
    ]

    try:
        print("[INFO] Converting AVI to MP4 with ffmpeg...")
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(f"[INFO] ffmpeg stdout:\n{completed.stdout}")
        print(f"[INFO] Conversion complete: {mp4_path}")
        # Optional: delete AVI after success
        avi_file.unlink(missing_ok=True)
    except subprocess.CalledProcessError as e:
        print("[ERROR] MP4 conversion failed.")
        print("------- ffmpeg stderr -------")
        print(e.stderr)
        print("-----------------------------")



# ---------- Main Analyzer ----------

def analyze_squat(video_path):
    """
    Analyze squat form from video:
    - Returns rep count.
    - Outputs: annotated MP4 video, CSV log, angle plot.
    """
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(model_complexity=1, enable_segmentation=False)
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[ERROR] Could not open video.")
        return 0

    os.makedirs('outputs', exist_ok=True)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[INFO] FPS: {fps:.2f}, Frames: {total_frames}, Resolution: {width}x{height}")

    avi_path = 'outputs/pose_output_video.avi'
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(avi_path, fourcc, fps if fps else 30.0, (width, height))

    rep_count = 0
    down = False
    min_knee_angle = 999  # Track lowest knee angle per rep
    log_data = []
    frame_idx = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        knee_angle, hip_angle = None, None
        feedback_msg = ""

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            lms = results.pose_landmarks.landmark

            # Use left landmarks, fallback to right
            hip, v1 = get_landmark_coords(lms, mp_pose.PoseLandmark.LEFT_HIP, width, height)
            knee, v2 = get_landmark_coords(lms, mp_pose.PoseLandmark.LEFT_KNEE, width, height)
            ankle, v3 = get_landmark_coords(lms, mp_pose.PoseLandmark.LEFT_ANKLE, width, height)
            shoulder, v4 = get_landmark_coords(lms, mp_pose.PoseLandmark.LEFT_SHOULDER, width, height)

            if not (good(v1) and good(v2) and good(v3) and good(v4)):
                hip, v1 = get_landmark_coords(lms, mp_pose.PoseLandmark.RIGHT_HIP, width, height)
                knee, v2 = get_landmark_coords(lms, mp_pose.PoseLandmark.RIGHT_KNEE, width, height)
                ankle, v3 = get_landmark_coords(lms, mp_pose.PoseLandmark.RIGHT_ANKLE, width, height)
                shoulder, v4 = get_landmark_coords(lms, mp_pose.PoseLandmark.RIGHT_SHOULDER, width, height)

            # Calculate angles
            knee_angle = calculate_angle(hip, knee, ankle)
            hip_angle = calculate_angle(shoulder, hip, knee)

            # Rep + depth logic
            if knee_angle is not None:
                if knee_angle < KNEE_BOTTOM and not down:
                    down = True
                    min_knee_angle = knee_angle
                if down:
                    min_knee_angle = min(min_knee_angle, knee_angle)
                if knee_angle > KNEE_TOP and down:
                    if min_knee_angle > DEPTH_THRESHOLD:
                        feedback_msg = "Go deeper!"
                    rep_count += 1
                    down = False
                    min_knee_angle = 999

                cv2.putText(frame, f'Knee: {int(knee_angle)} deg', (knee[0]-50, knee[1]-20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)

            if hip_angle is not None:
                cv2.putText(frame, f'Hip: {int(hip_angle)} deg', (hip[0]-50, hip[1]-20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)

            if hip_angle and hip_angle < 45:
                feedback_msg = "Keep chest up!"

        if feedback_msg:
            cv2.putText(frame, feedback_msg, (30, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        time_sec = frame_idx / fps
        log_data.append([
            frame_idx,
            round(time_sec, 2),
            round(knee_angle if knee_angle else 0, 1),
            round(hip_angle if hip_angle else 0, 1),
            feedback_msg
        ])

        cv2.putText(frame, f'Reps: {rep_count}', (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # Save CSV and plot
    save_csv(log_data)
    plot_knee_angles(log_data)

    # Convert AVI to MP4
    convert_to_mp4(avi_path, 'outputs/pose_output_video.mp4')

    print(f"[INFO] Analysis complete: {rep_count} reps counted.")
    return rep_count


# ---------- Script Entry ----------
if __name__ == "__main__":
    analyze_squat("squat_video.mp4")
