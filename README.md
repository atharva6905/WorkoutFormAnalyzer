# Workout Form Analyzer

Analyze squat form using pose estimation (MediaPipe + OpenCV). Counts reps, gives feedback, and generates an annotated video, CSV of joint angles, and a knee angle plot.

## 🔧 Tech Stack
- Frontend: React + Vite + TailwindCSS
- Backend: FastAPI, OpenCV, MediaPipe
- Output: Annotated video (.mp4), CSV, Matplotlib plot

## 📂 Features
- Reps counted from squat video
- Joint angles extracted and plotted
- Feedback per rep (in progress)
- CSV + video + plot download
- JSON API output

## 🚀 Running Locally

### Backend
```bash
cd workoutform-backend
pip install -r requirements.txt
uvicorn app:app --reload

### Frontend
cd workoutform-frontend
npm install
npm run dev
