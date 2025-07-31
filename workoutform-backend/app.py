"""
app.py - FastAPI Backend for Squat Analysis (Updated for MP4)
- POST /analyze: Upload a video, analyze it, return JSON results.
- Static files: Outputs can be accessed via URLs, e.g., /outputs/pose_output_video.mp4
"""

import os
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pose_video import analyze_squat
from fastapi.middleware.cors import CORSMiddleware

# Ensure required directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

app = FastAPI(title="Workout Form Analyzer", version="1.0")

# Allow frontend (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from outputs/ folder
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/")
def home():
    return {"message": "Workout Form Analyzer API is running."}


@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    try:
        # Save uploaded video to uploads/
        video_path = os.path.join("uploads", file.filename)
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run squat analysis (generates outputs in outputs/)
        reps = analyze_squat(video_path)

        # Collect output files
        output_files = ["pose_output_video.mp4", "angles_log.csv", "knee_angle_plot.png"]
        output_paths = {}
        for filename in output_files:
            src = os.path.join("outputs", filename)
            if os.path.exists(src):
                output_paths[filename] = f"/outputs/{filename}"

        return JSONResponse(content={
            "reps": reps,
            "video_url": output_paths.get("pose_output_video.mp4"),
            "csv_url": output_paths.get("angles_log.csv"),
            "plot_url": output_paths.get("knee_angle_plot.png")
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
