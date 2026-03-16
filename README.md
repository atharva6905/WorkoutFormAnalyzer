# Workout Form Analyzer

[![CI](https://github.com/atharva6905/WorkoutFormAnalyzer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/atharva6905/WorkoutFormAnalyzer/actions/workflows/ci.yml)

Upload an exercise video and get async form analysis with rep metrics, annotated video, CSV output, and angle plots.

## Architecture Overview

​```text
Browser
  │
  ▼
Frontend (React + Vite + Nginx)
  │
  ▼
Backend API (FastAPI)
  │
  ▼
Redis Queue (RQ)
  │
  ▼
Worker
  ├──────────────┐
  │              │
  ▼              ▼
Postgres    Filesystem (artifacts/)
​```

## Features

- Upload exercise videos from the browser with a drag-and-drop workflow
- Queue analysis jobs asynchronously so uploads return quickly
- Track job state with queued, processing, completed, and failed statuses
- Extract pose landmarks and joint-angle time series with MediaPipe and OpenCV
- Detect squat reps from processed knee-angle signals
- Generate annotated output video with overlays for pose, rep, and movement status
- Export frame-level angle data to CSV
- Generate a knee and hip angle plot with rep regions and thresholds
- Persist analyses and per-rep metrics in the database
- Serve artifacts and analysis results through a JSON API

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, React Router |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic Settings |
| Queue | Redis, RQ |
| DB | PostgreSQL |
| CV | OpenCV, MediaPipe, Matplotlib, NumPy |

## Local Setup

### Prerequisites

- Docker
- Docker Compose

### Steps

1. Clone the repo:

```bash
git clone https://github.com/atharva6905/WorkoutFormAnalyzer.git
cd WorkoutFormApp
```

2. Copy the environment template to `.env` and fill in values:

```bash
cp docker-compose.env.example .env
```

3. Start the full stack:

```bash
docker compose up --build
```

4. Database migrations are applied automatically by the backend entrypoint on startup.

5. Open the app:

```text
http://localhost:5173
```

## Manual Local Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Worker

```bash
cd backend
python worker.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

| Name | Description | Example |
| --- | --- | --- |
| `POSTGRES_USER` | PostgreSQL username for Docker Compose | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password for Docker Compose | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `workoutdb` |
| `DATABASE_URL` | SQLAlchemy database connection string | `postgresql://postgres:postgres@postgres:5432/workoutdb` |
| `REDIS_URL` | Redis connection string for API and worker | `redis://redis:6379` |
| `ARTIFACT_DIR` | Directory used to store generated output artifacts | `artifacts` |
| `BACKEND_HOST` | Public backend base URL used when building artifact links | `http://localhost:8000` |
| `DEBUG` | Enables debug-level backend logging when true | `True` |
| `VITE_API_URL` | Frontend API base URL for local development | `http://localhost:8000` |

## How Async Job Flow Works

When a user uploads a video, the backend immediately creates an `Analysis` record with status `queued`, stores the uploaded file on disk, and pushes a job into Redis. An RQ worker picks that job up, marks the analysis as `processing`, extracts landmarks, smooths angle signals, detects reps, generates artifacts, stores rep metrics and summary data in Postgres, and finally marks the job as `completed` or `failed`. The frontend polls the analysis status until processing finishes, then loads the full result page and artifact links.

## API Route Summary

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check endpoint |
| `POST` | `/analyses` | Create a new analysis job from an uploaded video |
| `GET` | `/analyses` | List recent analyses |
| `GET` | `/analyses/{analysis_id}` | Return full analysis details, summary, artifacts, and rep metrics |
| `GET` | `/analyses/{analysis_id}/status` | Return current job status |
| `GET` | `/analyses/{analysis_id}/artifacts/video` | Stream the annotated output video |
| `GET` | `/analyses/{analysis_id}/artifacts/csv` | Download the CSV report |
| `GET` | `/analyses/{analysis_id}/artifacts/plot` | Return the generated angle plot image |

## How To Run Tests

```bash
cd backend
pytest
```

For fast runs that skip slow integration tests:

```bash
cd backend
pytest -m "not slow"
```

## Output Artifacts

- `annotated.mp4`: Annotated output video with pose skeleton, knee and hip angles, rep number, current movement status, and active-rep highlighting
- `angles.csv`: Frame-level report with `frame_index`, `timestamp_seconds`, `knee_angle`, `hip_angle`, `landmark_confidence`, and `valid_frame`
- `plot.png`: Plot of knee and hip angles over frame index, including rep-window shading and threshold lines for squat depth and standing position


## Sample Screenshots

Add screenshots here after the first successful end-to-end run:

- Upload page
- Processing state
- Completed result page
- Annotated video frame
