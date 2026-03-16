"""Analysis ORM model"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnalysisStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=AnalysisStatus.QUEUED.value)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False, default="squat")
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    annotated_video_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    csv_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    plot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rep_metrics: Mapped[list["RepMetric"]] = relationship("RepMetric", back_populates="analysis")
