"""Analysis CRUD and job creation endpoints"""

import json
import logging
import multiprocessing
import sys

if sys.platform == "win32":
    _original_get_context = multiprocessing.get_context
    multiprocessing.get_context = lambda method=None: _original_get_context("spawn" if method == "fork" else method)

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from redis import Redis
from redis.exceptions import RedisError
from rq import Queue
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.analysis import (
    AnalysisCreateResponse,
    AnalysisDetailResponse,
    AnalysisListItem,
    AnalysisStatusResponse,
    AnalysisSummary,
    RepMetricResponse,
)
from app.schemas.common import ArtifactURLs
from app.services import analysis_service, artifact_service
from app.workers.jobs import run_analysis


router = APIRouter()
logger = logging.getLogger(__name__)


def get_queue() -> Queue:
    redis_conn = Redis.from_url(settings.REDIS_URL)
    return Queue("analysis", connection=redis_conn)


@router.post("", response_model=AnalysisCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    file: UploadFile = File(...),
    exercise_type: str = Form("squat"),
    db: Session = Depends(get_db),
) -> AnalysisCreateResponse:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must be a video.")

    analysis = analysis_service.create_analysis(
        db,
        original_filename=file.filename,
        exercise_type=exercise_type,
        video_path="",
    )
    logger.info("analysis_created analysis_id=%s exercise_type=%s", analysis.id, exercise_type)

    artifact_service.create_artifact_dir(analysis.id)
    video_path = artifact_service.get_input_video_path(analysis.id, file.filename or "")

    with open(video_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    analysis.video_path = str(video_path)
    db.commit()
    db.refresh(analysis)

    try:
        queue = get_queue()
        job = queue.enqueue(run_analysis, analysis.id, job_timeout=300)
        logger.info("analysis_enqueued analysis_id=%s job_id=%s", analysis.id, job.id)
    except RedisError:
        logger.warning("analysis_enqueue_failed analysis_id=%s", analysis.id, exc_info=True)

    return AnalysisCreateResponse.model_validate(analysis)


@router.get("", response_model=list[AnalysisListItem])
def list_analyses(db: Session = Depends(get_db)) -> list[AnalysisListItem]:
    analyses = analysis_service.list_analyses(db)
    return [AnalysisListItem.model_validate(analysis) for analysis in analyses]


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisDetailResponse:
    analysis = analysis_service.get_analysis(db, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")

    summary = None
    if analysis.summary_json:
        try:
            summary = AnalysisSummary.model_validate(json.loads(analysis.summary_json))
        except json.JSONDecodeError:
            summary = None

    artifact_urls = None
    if analysis.annotated_video_path or analysis.csv_path or analysis.plot_path:
        artifact_urls = ArtifactURLs(
            annotated_video_url=artifact_service.build_artifact_url(analysis.annotated_video_path),
            csv_url=artifact_service.build_artifact_url(analysis.csv_path),
            plot_url=artifact_service.build_artifact_url(analysis.plot_path),
        )

    rep_metrics = sorted(analysis.rep_metrics, key=lambda item: item.rep_index)

    return AnalysisDetailResponse(
        id=analysis.id,
        status=analysis.status,
        exercise_type=analysis.exercise_type,
        summary=summary,
        artifacts=artifact_urls,
        rep_metrics=[RepMetricResponse.model_validate(rep_metric) for rep_metric in rep_metrics],
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisStatusResponse:
    analysis = analysis_service.get_analysis(db, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")

    return AnalysisStatusResponse.model_validate(analysis)
