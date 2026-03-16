import math

import numpy as np

from app.models.analysis import Analysis
from app.services.analysis_service import update_analysis_status
from app.services.pose_service import calculate_angle
from app.services.rep_detection import detect_reps
from app.services.signal_processing import fill_gaps, smooth_signal


def test_calculate_angle_right_angle():
    angle = calculate_angle((1, 0), (0, 0), (0, 1))

    assert abs(angle - 90.0) < 1.0


def test_calculate_angle_straight_line():
    angle = calculate_angle((0, 0), (1, 0), (2, 0))

    assert abs(angle - 180.0) < 1.0


def test_smooth_signal_reduces_noise():
    rng = np.random.default_rng(42)
    x = np.linspace(0, 4 * math.pi, 200)
    noisy_signal = np.sin(x) + rng.normal(0, 0.35, size=x.shape[0])

    smoothed = smooth_signal(noisy_signal.tolist(), window=7)

    assert np.var(smoothed) < np.var(noisy_signal)


def test_fill_gaps_interpolates_short_gaps():
    values = [1.0, None, None, 4.0, 5.0]

    filled = fill_gaps(values, max_gap=3)

    assert filled[1] is not None
    assert filled[2] is not None
    assert 1.0 < filled[1] < 4.0
    assert 1.0 < filled[2] < 4.0


def test_fill_gaps_preserves_long_gaps():
    values = [1.0] + [None] * 8 + [10.0]

    filled = fill_gaps(values, max_gap=5)

    assert all(value is None for value in filled[1:9])


def test_detect_reps_on_synthetic_signal():
    cycle = (
        [170.0] * 5
        + np.linspace(170.0, 80.0, 25).tolist()
        + np.linspace(80.0, 170.0, 25).tolist()
        + [170.0] * 5
    )
    signal = cycle * 3

    reps = detect_reps(signal, fps=30.0)

    assert len(reps) == 3


def test_detect_reps_rejects_noise():
    rng = np.random.default_rng(7)
    signal = (160.0 + rng.normal(0, 5.0, size=180)).tolist()

    reps = detect_reps(signal, fps=30.0)

    assert len(reps) == 0


def test_analysis_status_transitions(db_session):
    analysis = Analysis(
        status="queued",
        exercise_type="squat",
        original_filename="sample.mp4",
        video_path="artifacts/test/input.mp4",
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    processing = update_analysis_status(db_session, analysis.id, "processing")
    assert processing is not None
    assert processing.status == "processing"

    completed = update_analysis_status(db_session, analysis.id, "completed")

    assert completed is not None
    assert completed.status == "completed"
