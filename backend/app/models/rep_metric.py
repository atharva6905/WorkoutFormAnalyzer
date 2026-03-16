"""RepMetric ORM model"""

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RepMetric(Base):
    __tablename__ = "rep_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id"), nullable=False, index=True)
    rep_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_frame: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_frame: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_knee_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_knee_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_hip_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_hip_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="rep_metrics")
