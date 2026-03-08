import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app import db
from app.models import Anomaly, Event, Summary, Upload, User
from app.services.anomaly import detect_anomalies
from app.services.ai_summary import (
    generate_detection_notes_summary,
    generate_executive_summary,
)
from app.services.parser import parse_zscaler_lines
from app.services.storage import save_upload_file
from app.services.summary import generate_summary_metrics

uploads_bp = Blueprint("uploads", __name__, url_prefix="/uploads")


def _format_bytes_short(byte_count: int) -> str:
    if byte_count >= 1024 * 1024:
        return f"{round(byte_count / (1024 * 1024), 1)}MB"
    if byte_count >= 1024:
        return f"{round(byte_count / 1024, 1)}KB"
    return f"{byte_count}B"


@uploads_bp.post("")
@jwt_required()
def upload_log_file():
    file_obj = request.files.get("file")
    if file_obj is None or not file_obj.filename:
        return jsonify({"error": "file is required"}), 400

    source = (request.form.get("source") or "zscaler").strip().lower()
    if source != "zscaler":
        return jsonify({"error": "only zscaler source is supported in this stage"}), 400

    user_identity = str(get_jwt_identity() or "").strip()
    user = db.session.scalar(select(User).where(User.public_id == user_identity))
    if user is None and user_identity.isdigit():
        user = db.session.get(User, int(user_identity))
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

        detection_result = detect_anomalies(parsed_events)
        if isinstance(detection_result, dict):
            detected_anomalies = detection_result.get("anomalies", [])
            detection_notes = detection_result.get("notes", [])
        else:
            detected_anomalies = detection_result
            detection_notes = []

        anomaly_models = []
        anomaly_response_items = []
        for anomaly_data in detected_anomalies:
            event_index = anomaly_data.get("event_index")
            if event_index is None or event_index >= len(event_models):
                continue
            anomaly_type = anomaly_data.get("anomaly_type") or anomaly_data.get("type")
            explanation = anomaly_data.get("description") or anomaly_data.get("explanation") or ""
            affected_lines = anomaly_data.get("affectedLines") or [event_index + 1]
            detection_method = anomaly_data.get("detectionMethod") or "rule_engine"
            if not anomaly_type:
                continue

            anomaly_model = Anomaly(
                upload_id=upload.id,
                event_id=event_models[event_index].id,
                anomaly_type=anomaly_type,
                severity=anomaly_data["severity"],
                score=anomaly_data["confidence"],
                description=explanation,
            )
            anomaly_models.append(anomaly_model)
            anomaly_response_items.append(
                {
                    "anomaly": anomaly_model,
                    "event_row": event_index + 1,
                    "affected_lines": affected_lines,
                    "detection_method": detection_method,
                }
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

    anomaly_payloads_for_ai = []
    for item in anomaly_response_items[:50]:
        row = int(item["event_row"])
        event = parsed_events[row - 1] if 0 < row <= len(parsed_events) else {}
        username = event.get("username") or "unknown_user"
        source_ip = event.get("source_ip") or "unknown_ip"
        destination = event.get("destination") or "unknown_destination"
        bytes_transferred = int(event.get("bytes_transferred") or 0)
        detail = (
            item["anomaly"].description
            or f"destination={destination}, bytes={_format_bytes_short(bytes_transferred)}"
        )

        anomaly_payloads_for_ai.append(
            {
                "row": row,
                "type": item["anomaly"].anomaly_type,
                "severity": (item["anomaly"].severity or "medium").upper(),
                "confidence": f"{round(float(item['anomaly'].score or 0) * 100)}%",
                "entity": f"{username}/{source_ip}",
                "detail": detail,
            }
        )

    blocked_events_for_ai = [
        {
            "user": event.get("username") or "unknown",
            "destination": event.get("destination") or "unknown",
            "category": event.get("category") or "Unknown",
        }
        for event in parsed_events
        if (event.get("action") or "").upper() == "BLOCK"
    ]

    executive_summary = generate_executive_summary(
        metrics,
        anomaly_payloads_for_ai,
        blocked_events_for_ai,
    )
    detection_notes_summary = generate_detection_notes_summary(
        detection_notes,
        anomaly_payloads_for_ai,
    )

    events_preview = []
    for event in parsed_events[:200]:
        event_time = event.get("event_time")
        events_preview.append(
            {
                "event_time": event_time.isoformat() if event_time else None,
                "username": event.get("username"),
                "source_ip": event.get("source_ip"),
                "destination": event.get("destination"),
                "action": event.get("action"),
                "category": event.get("category"),
                "bytes_transferred": event.get("bytes_transferred"),
            }
        )

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
                "detection_notes": detection_notes[:10],
                "detection_notes_summary": detection_notes_summary,
                "events_preview": events_preview,
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
                "ai_summary": executive_summary,
                "anomalies": [
                    {
                        "event_row": item["event_row"],
                        "affectedLines": item["affected_lines"],
                        "detectionMethod": item["detection_method"],
                        "type": item["anomaly"].anomaly_type,
                        "event_id": item["anomaly"].event_id,
                        "anomaly_type": item["anomaly"].anomaly_type,
                        "severity": item["anomaly"].severity,
                        "confidence": item["anomaly"].score,
                        "explanation": item["anomaly"].description,
                        "description": item["anomaly"].description,
                    }
                    for item in anomaly_response_items[:20]
                ],
            }
        ),
        201,
    )
