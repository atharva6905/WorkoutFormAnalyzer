"""Shared Pydantic types"""

from pydantic import BaseModel, ConfigDict


class ArtifactURLs(BaseModel):
    annotated_video_url: str | None = None
    csv_url: str | None = None
    plot_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
