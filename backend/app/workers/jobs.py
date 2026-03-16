"""RQ worker job definitions"""

import json
import logging
from statistics import mean

from app.db.session import SessionLocal
from app.models.rep_metric import RepMetric
from app.services import (
    analysis_service,
    artifact_service,
    pose_service,
    rep_detection,
    report_generation,
    signal_processing,
    video_annotation,
)


logger = logging.getLogger(__name__)


def run_analysis(analysis_id: str, db=None) -> None:
    owned_db = db is None
    if owned_db:
        db = SessionLocal()

    logger.info("analysis_job.start analysis_id=%s", analysis_id)

    try:
        analysis = analysis_service.get_analysis(db, analysis_id)
        if analysis is None:
            logger.error("analysis_job.missing_analysis analysis_id=%s", analysis_id)
            return

        logger.info("analysis_job.set_processing analysis_id=%s", analysis_id)
        analysis = analysis_service.update_analysis_status(db, analysis_id, "processing") or analysis
        logger.info("analysis_job.set_processing.complete analysis_id=%s status=%s", analysis_id, analysis.status)

        try:
            video_path = analysis.video_path
            if not video_path:
                raise FileNotFoundError("Analysis has no input video path.")

            logger.info("analysis_job.video_metadata analysis_id=%s", analysis_id)
            metadata = pose_service.get_video_metadata(video_path)
            fps = float(metadata["fps"])
            logger.info(
                "analysis_job.video_metadata.complete analysis_id=%s fps=%s width=%s height=%s total_frames=%s",
                analysis_id,
                metadata["fps"],
                metadata["width"],
                metadata["height"],
                metadata["total_frames"],
            )

            logger.info("analysis_job.extract_landmarks analysis_id=%s", analysis_id)
            frame_data, raw_landmarks = pose_service.extract_landmarks(video_path)
            logger.info("analysis_job.extract_landmarks.complete analysis_id=%s frames=%s", analysis_id, len(frame_data))

            logger.info("analysis_job.preprocess_knee analysis_id=%s", analysis_id)
            knee_angles = signal_processing.preprocess_angles(frame_data, "knee_angle")
            logger.info("analysis_job.preprocess_knee.complete analysis_id=%s", analysis_id)

            logger.info("analysis_job.preprocess_hip analysis_id=%s", analysis_id)
            hip_angles = signal_processing.preprocess_angles(frame_data, "hip_angle")
            logger.info("analysis_job.preprocess_hip.complete analysis_id=%s", analysis_id)

            logger.info("analysis_job.detect_reps analysis_id=%s", analysis_id)
            rep_windows = rep_detection.detect_reps(knee_angles, fps)
            logger.info("analysis_job.detect_reps.complete analysis_id=%s count=%s", analysis_id, len(rep_windows))

            logger.info("analysis_job.extract_rep_metrics analysis_id=%s", analysis_id)
            rep_metrics = rep_detection.extract_rep_metrics(rep_windows, knee_angles, hip_angles, frame_data)
            logger.info("analysis_job.extract_rep_metrics.complete analysis_id=%s count=%s", analysis_id, len(rep_metrics))

            logger.info("analysis_job.save_rep_metrics analysis_id=%s count=%s", analysis_id, len(rep_metrics))
            rep_metric_rows = [
                RepMetric(
                    analysis_id=analysis_id,
                    rep_index=rep_metric["rep_index"],
                    start_frame=rep_metric["start_frame"],
                    end_frame=rep_metric["end_frame"],
                    min_knee_angle=rep_metric["min_knee_angle"],
                    max_knee_angle=rep_metric["max_knee_angle"],
                    min_hip_angle=rep_metric["min_hip_angle"],
                    max_hip_angle=rep_metric["max_hip_angle"],
                    confidence_score=rep_metric["confidence_score"],
                    notes=rep_metric["notes"],
                )
                for rep_metric in rep_metrics
            ]
            if rep_metric_rows:
                db.add_all(rep_metric_rows)
                db.commit()
            logger.info("analysis_job.save_rep_metrics.complete analysis_id=%s", analysis_id)

            logger.info("analysis_job.annotate_video analysis_id=%s", analysis_id)
            annotated_path = artifact_service.get_artifact_path(analysis_id, "annotated.mp4")
            video_annotation.annotate_video(
                video_path,
                str(annotated_path),
                frame_data,
                rep_windows,
                raw_landmarks,
            )
            logger.info("analysis_job.annotate_video.complete analysis_id=%s path=%s", analysis_id, annotated_path)

            logger.info("analysis_job.generate_csv analysis_id=%s", analysis_id)
            csv_path = artifact_service.get_artifact_path(analysis_id, "angles.csv")
            report_generation.generate_csv(frame_data, str(csv_path))
            logger.info("analysis_job.generate_csv.complete analysis_id=%s path=%s", analysis_id, csv_path)

            logger.info("analysis_job.generate_plot analysis_id=%s", analysis_id)
            plot_path = artifact_service.get_artifact_path(analysis_id, "plot.png")
            report_generation.generate_plot(frame_data, rep_windows, str(plot_path))
            logger.info("analysis_job.generate_plot.complete analysis_id=%s path=%s", analysis_id, plot_path)

            confidence_scores = [
                rep_metric["confidence_score"]
                for rep_metric in rep_metrics
                if rep_metric["confidence_score"] is not None
            ]
            summary = {
                "rep_count": len(rep_windows),
                "avg_confidence": mean(confidence_scores) if confidence_scores else None,
            }
            logger.info("analysis_job.summary.complete analysis_id=%s rep_count=%s", analysis_id, summary["rep_count"])

            logger.info("analysis_job.update_results analysis_id=%s", analysis_id)
            analysis_service.update_analysis_results(
                db,
                analysis_id,
                str(annotated_path),
                str(csv_path),
                str(plot_path),
                json.dumps(summary),
            )
            logger.info("analysis_job.update_results.complete analysis_id=%s", analysis_id)

            logger.info("analysis_job.set_completed analysis_id=%s", analysis_id)
            analysis_service.update_analysis_status(db, analysis_id, "completed")
            logger.info("analysis_job.set_completed.complete analysis_id=%s", analysis_id)

        except Exception as exc:
            logger.error("analysis_job.failed analysis_id=%s", analysis_id, exc_info=True)
            analysis_service.mark_analysis_failed(db, analysis_id, str(exc))

    finally:
        if owned_db:
            db.close()
            logger.info("analysis_job.closed_db analysis_id=%s", analysis_id)
