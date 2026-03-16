"""FastAPI app entry point."""

import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging import setup_logging


logger = logging.getLogger(__name__)

app = FastAPI(title="Workout Form Analyzer", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="")
app.include_router(analyses_router, prefix="/analyses", tags=["analyses"])
app.include_router(artifacts_router, prefix="/analyses", tags=["artifacts"])


@app.on_event("startup")
def startup_event() -> None:
    setup_logging()
    os.makedirs(settings.ARTIFACT_DIR, exist_ok=True)
    logger.info("Workout Form Analyzer starting up")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
