"""Pytest fixtures and test setup.

Tests use a separate SQLite test database.
"""

from collections.abc import Generator
import os

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

TEST_DATABASE_URL = "sqlite:///./test.db"

os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)
os.environ["DEBUG"] = "False"

import app.models  # noqa: F401
from app.api import deps
from app.core.config import settings
from app.db.base import Base
from app.main import app


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Generator[object, None, None]:
    original_database_url = settings.DATABASE_URL
    monkeypatch.setattr(settings, "DATABASE_URL", TEST_DATABASE_URL)
    yield settings
    monkeypatch.setattr(settings, "DATABASE_URL", original_database_url)


@pytest.fixture
def test_engine(test_settings: object) -> Generator[object, None, None]:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine: object) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[deps.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_video(tmp_path) -> str:
    video_path = tmp_path / "sample.avi"
    frame_width = 640
    frame_height = 480
    fps = 30.0
    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"XVID"),
        fps,
        (frame_width, frame_height),
    )

    for _ in range(30):
        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        writer.write(frame)

    writer.release()
    return str(video_path)
