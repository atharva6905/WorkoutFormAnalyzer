"""Artifact retrieval endpoints"""

import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import analysis_service


router = APIRouter()


def _get_existing_artifact_path(db: Session, analysis_id: str, field_name: str) -> str:
    analysis = analysis_service.get_analysis(db, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")

    artifact_path = getattr(analysis, field_name)
    if not artifact_path or not os.path.exists(artifact_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found.")

    return artifact_path


@router.get("/{analysis_id}/artifacts/video")
def get_artifact_video(analysis_id: str, db: Session = Depends(get_db)) -> FileResponse:
    artifact_path = _get_existing_artifact_path(db, analysis_id, "annotated_video_path")
    return FileResponse(artifact_path, media_type="video/mp4")


@router.get("/{analysis_id}/artifacts/csv")
def get_artifact_csv(analysis_id: str, db: Session = Depends(get_db)) -> FileResponse:
    artifact_path = _get_existing_artifact_path(db, analysis_id, "csv_path")
    return FileResponse(
        artifact_path,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="angles.csv"'},
    )


@router.get("/{analysis_id}/artifacts/plot")
def get_artifact_plot(analysis_id: str, db: Session = Depends(get_db)) -> FileResponse:
    artifact_path = _get_existing_artifact_path(db, analysis_id, "plot_path")
    return FileResponse(artifact_path, media_type="image/png")
