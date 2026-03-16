from pathlib import Path


def _create_analysis(client, sample_video: str) -> dict:
    video_path = Path(sample_video)
    with video_path.open("rb") as video_file:
        response = client.post(
            "/analyses",
            files={"file": (video_path.name, video_file, "video/x-msvideo")},
            data={"exercise_type": "squat"},
        )

    assert response.status_code == 202
    return response.json()


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_analysis_returns_202(client, sample_video):
    body = _create_analysis(client, sample_video)

    assert "id" in body
    assert body["status"] == "queued"
    assert body["exercise_type"] == "squat"


def test_create_analysis_rejects_non_video(client, tmp_path):
    text_path = tmp_path / "notes.txt"
    text_path.write_text("not a video", encoding="utf-8")

    with text_path.open("rb") as text_file:
        response = client.post(
            "/analyses",
            files={"file": (text_path.name, text_file, "text/plain")},
            data={"exercise_type": "squat"},
        )

    assert response.status_code == 400


def test_get_analysis_status(client, sample_video):
    created = _create_analysis(client, sample_video)

    response = client.get(f"/analyses/{created['id']}/status")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert "status" in body


def test_get_analysis_detail(client, sample_video):
    created = _create_analysis(client, sample_video)

    response = client.get(f"/analyses/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert "status" in body
    assert isinstance(body["rep_metrics"], list)
    assert "artifacts" in body


def test_get_missing_analysis_returns_404(client):
    response = client.get("/analyses/nonexistent-uuid")

    assert response.status_code == 404


def test_get_artifact_before_processing_returns_404(client, sample_video):
    created = _create_analysis(client, sample_video)
    analysis_id = created["id"]

    video_response = client.get(f"/analyses/{analysis_id}/artifacts/video")
    csv_response = client.get(f"/analyses/{analysis_id}/artifacts/csv")
    plot_response = client.get(f"/analyses/{analysis_id}/artifacts/plot")

    assert video_response.status_code == 404
    assert csv_response.status_code == 404
    assert plot_response.status_code == 404


def test_list_analyses(client, sample_video):
    _create_analysis(client, sample_video)
    _create_analysis(client, sample_video)

    response = client.get("/analyses")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 2
