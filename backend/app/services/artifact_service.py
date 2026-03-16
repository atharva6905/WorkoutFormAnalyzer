"""Artifact directory and path management"""

from pathlib import Path

from app.core.config import settings


def create_artifact_dir(analysis_id: str) -> Path:
    artifact_dir = Path(settings.ARTIFACT_DIR) / analysis_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir


def get_artifact_path(analysis_id: str, filename: str) -> Path:
    return Path(settings.ARTIFACT_DIR) / analysis_id / filename


def artifact_exists(analysis_id: str, filename: str) -> bool:
    return get_artifact_path(analysis_id, filename).exists()


def get_input_video_path(analysis_id: str, original_filename: str) -> Path:
    sanitized_name = Path(original_filename).name
    extension = Path(sanitized_name).suffix
    filename = f"input{extension}" if extension else "input"
    return get_artifact_path(analysis_id, filename)


def build_artifact_urls(analysis_id: str, base_url: str) -> dict[str, str]:
    base = base_url.rstrip("/")
    urls: dict[str, str] = {}

    if artifact_exists(analysis_id, "annotated.mp4"):
        urls["annotated_video_url"] = f"{base}/analyses/{analysis_id}/artifacts/video"
    if artifact_exists(analysis_id, "angles.csv"):
        urls["csv_url"] = f"{base}/analyses/{analysis_id}/artifacts/csv"
    if artifact_exists(analysis_id, "plot.png"):
        urls["plot_url"] = f"{base}/analyses/{analysis_id}/artifacts/plot"

    return urls


def build_artifact_url(path: str | None) -> str | None:
    if not path:
        return None

    path_obj = Path(path)
    analysis_id = path_obj.parent.name
    normalized_name = path_obj.name.lower()

    if normalized_name.endswith(".mp4"):
        return build_artifact_urls(analysis_id, settings.BACKEND_HOST).get("annotated_video_url")
    if normalized_name.endswith(".csv"):
        return build_artifact_urls(analysis_id, settings.BACKEND_HOST).get("csv_url")
    if normalized_name.endswith(".png"):
        return build_artifact_urls(analysis_id, settings.BACKEND_HOST).get("plot_url")

    return None
