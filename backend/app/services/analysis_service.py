"""DB operations for Analysis records"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis


def create_analysis(db: Session, original_filename: str | None, exercise_type: str, video_path: str | None) -> Analysis:
    analysis = Analysis(
        original_filename=original_filename,
        exercise_type=exercise_type,
        video_path=video_path,
        status="queued",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis(db: Session, analysis_id: str) -> Analysis | None:
    return db.get(Analysis, analysis_id)


def list_analyses(db: Session, limit: int = 20) -> list[Analysis]:
    stmt = select(Analysis).order_by(Analysis.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def update_analysis_status(db: Session, analysis_id: str, status: str) -> Analysis | None:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        return None

    analysis.status = status
    analysis.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(analysis)
    return analysis


def update_analysis_results(
    db: Session,
    analysis_id: str,
    annotated_video_path: str | None,
    csv_path: str | None,
    plot_path: str | None,
    summary_json: str | None,
) -> Analysis | None:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        return None

    analysis.annotated_video_path = annotated_video_path
    analysis.csv_path = csv_path
    analysis.plot_path = plot_path
    analysis.summary_json = summary_json
    analysis.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(analysis)
    return analysis


def mark_analysis_failed(db: Session, analysis_id: str, error_message: str | None) -> Analysis | None:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        return None

    analysis.status = "failed"
    analysis.error_message = error_message
    analysis.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(analysis)
    return analysis
