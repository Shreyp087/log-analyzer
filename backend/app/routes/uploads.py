import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models import Anomaly, Event, Summary, Upload, User
from app.services.anomaly import detect_anomalies
from app.services.parser import parse_zscaler_lines
from app.services.storage import save_upload_file
from app.services.summary import generate_summary_metrics

uploads_bp = Blueprint("uploads", __name__, url_prefix="/uploads")


@uploads_bp.post("")
@jwt_required()
def upload_log_file():
    file_obj = request.files.get("file")
    if file_obj is None or not file_obj.filename:
        return jsonify({"error": "file is required"}), 400

    source = (request.form.get("source") or "zscaler").strip().lower()
    if source != "zscaler":
        return jsonify({"error": "only zscaler source is supported in this stage"}), 400

    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "user not found"}), 404

    try:
        upload = Upload(
            user_id=user.id,
            filename=file_obj.filename,
            source=source,
            status="uploaded",
        )
        db.session.add(upload)
        db.session.flush()

        file_path = save_upload_file(file_obj, current_app.config["UPLOAD_DIR"], upload.id)
        upload.file_path = file_path

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        parsed_events, parse_errors = parse_zscaler_lines(lines)
        event_models = [Event(upload_id=upload.id, **event_data) for event_data in parsed_events]
        db.session.add_all(event_models)
        db.session.flush()

        detected_anomalies = detect_anomalies(parsed_events)
        anomaly_models = []
        for anomaly_data in detected_anomalies:
            event_index = anomaly_data.get("event_index")
            if event_index is None or event_index >= len(event_models):
                continue

            anomaly_models.append(
                Anomaly(
                    upload_id=upload.id,
                    event_id=event_models[event_index].id,
                    anomaly_type=anomaly_data["anomaly_type"],
                    severity=anomaly_data["severity"],
                    score=anomaly_data["confidence"],
                    description=anomaly_data["description"],
                )
            )
        db.session.add_all(anomaly_models)

        metrics = generate_summary_metrics(parsed_events)
        summary = Summary(
            upload_id=upload.id,
            total_events=metrics["total_events"],
            total_anomalies=len(anomaly_models),
            allowed_count=metrics["allowed_events"],
            blocked_count=metrics["blocked_events"],
            unique_source_ips=metrics["unique_ips"],
            top_categories=metrics["top_categories"],
            top_destinations=metrics["top_destinations"],
            top_source_ips=metrics["top_source_ips"],
        )
        db.session.add(summary)

        upload.status = "processed_with_errors" if parse_errors else "processed"
        upload.processed_at = datetime.utcnow()

        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "failed to process upload", "details": str(exc)}), 500

    return (
        jsonify(
            {
                "upload_id": upload.id,
                "filename": upload.filename,
                "stored_file": os.path.basename(upload.file_path or ""),
                "status": upload.status,
                "events_saved": len(parsed_events),
                "anomalies_detected": len(anomaly_models),
                "parse_errors_count": len(parse_errors),
                "parse_errors": parse_errors[:20],
                "summary": {
                    "total_events": summary.total_events,
                    "total_anomalies": summary.total_anomalies,
                    "blocked_events": summary.blocked_count,
                    "allowed_events": summary.allowed_count,
                    "unique_ips": summary.unique_source_ips,
                    "top_categories": summary.top_categories,
                    "top_destinations": summary.top_destinations,
                    "top_source_ips": summary.top_source_ips,
                },
                "anomalies": [
                    {
                        "event_id": anomaly.event_id,
                        "anomaly_type": anomaly.anomaly_type,
                        "severity": anomaly.severity,
                        "confidence": anomaly.score,
                        "description": anomaly.description,
                    }
                    for anomaly in anomaly_models[:20]
                ],
            }
        ),
        201,
    )
