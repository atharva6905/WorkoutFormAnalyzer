import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.analysis import Analysis
from app.models.rep_metric import RepMetric
from app.workers.jobs import run_analysis


@pytest.mark.slow
def test_full_analysis_pipeline(db_session, sample_video, tmp_path, monkeypatch):
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setattr(settings, "ARTIFACT_DIR", str(artifact_dir))

    analysis = Analysis(
        status="queued",
        exercise_type="squat",
        original_filename=Path(sample_video).name,
        video_path=sample_video,
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    run_analysis(analysis.id, db=db_session)

    db_session.expire_all()
    updated_analysis = db_session.get(Analysis, analysis.id)

    assert updated_analysis is not None
    assert updated_analysis.status == "completed"
    assert updated_analysis.annotated_video_path is not None
    assert Path(updated_analysis.annotated_video_path).exists()
    assert updated_analysis.csv_path is not None
    assert Path(updated_analysis.csv_path).exists()
    assert updated_analysis.plot_path is not None
    assert Path(updated_analysis.plot_path).exists()
    assert updated_analysis.summary_json is not None

    summary = json.loads(updated_analysis.summary_json)
    assert "rep_count" in summary

    rep_metrics = db_session.scalars(
        select(RepMetric).where(RepMetric.analysis_id == analysis.id)
    ).all()
    assert len(rep_metrics) >= 0
    assert updated_analysis.error_message is None


def test_failed_analysis_marks_as_failed(db_session, tmp_path, monkeypatch):
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setattr(settings, "ARTIFACT_DIR", str(artifact_dir))

    analysis = Analysis(
        status="queued",
        exercise_type="squat",
        original_filename="missing.mp4",
        video_path=str(tmp_path / "missing.mp4"),
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    run_analysis(analysis.id, db=db_session)

    db_session.expire_all()
    updated_analysis = db_session.get(Analysis, analysis.id)

    assert updated_analysis is not None
    assert updated_analysis.status == "failed"
    assert updated_analysis.error_message is not None
