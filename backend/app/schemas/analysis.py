"""Pydantic schemas for analysis endpoints"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import ArtifactURLs


class AnalysisCreateResponse(BaseModel):
    id: str
    status: str
    exercise_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisStatusResponse(BaseModel):
    id: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class RepMetricResponse(BaseModel):
    rep_index: int
    start_frame: int | None = None
    end_frame: int | None = None
    min_knee_angle: float | None = None
    max_knee_angle: float | None = None
    min_hip_angle: float | None = None
    max_hip_angle: float | None = None
    confidence_score: float | None = None
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisSummary(BaseModel):
    rep_count: int | None = None
    avg_confidence: float | None = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisDetailResponse(BaseModel):
    id: str
    status: str
    exercise_type: str
    summary: AnalysisSummary | None = None
    artifacts: ArtifactURLs | None = None
    rep_metrics: list[RepMetricResponse]
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisListItem(BaseModel):
    id: str
    status: str
    exercise_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
