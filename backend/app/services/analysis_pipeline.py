import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from app import db
from app.models import Anomaly, Event, Summary, Upload
from app.services.ai_enrichment import enrich_high_priority_anomalies
from app.services.ai_summary import (
    generate_detection_notes_summary,
    generate_executive_summary,
)
from app.services.anomaly import detect_anomalies
from app.services.parser import parse_zscaler_lines
from app.services.summary import generate_summary_metrics

logger = logging.getLogger(__name__)


def _format_bytes_short(byte_count: int) -> str:
    if byte_count >= 1024 * 1024:
        return f"{round(byte_count / (1024 * 1024), 1)}MB"
    if byte_count >= 1024:
        return f"{round(byte_count / 1024, 1)}KB"
    return f"{byte_count}B"


def _clear_previous_results(upload: Upload) -> None:
    if upload.summary is not None:
        db.session.delete(upload.summary)

    for anomaly in list(upload.anomalies):
        db.session.delete(anomaly)

    for event in list(upload.events):
        db.session.delete(event)

    db.session.flush()


def _cleanup_file(upload: Upload, file_path: str) -> None:
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        upload.file_path = None
        db.session.commit()
    except OSError as exc:
        logger.warning("Failed to delete uploaded file '%s': %s", file_path, exc)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning("Failed to finalize upload cleanup for upload_id=%s: %s", upload.id, exc)
        db.session.rollback()


def process_upload_analysis(upload: Upload) -> Dict[str, Any]:
    if not upload.file_path:
        raise FileNotFoundError("uploaded file path is missing for this upload")

    file_path = upload.file_path
    if not os.path.exists(file_path):
        raise FileNotFoundError("uploaded file was not found on disk")

    stored_file = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    parsed_events, parse_errors = parse_zscaler_lines(lines)

    _clear_previous_results(upload)
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

    anomaly_models: List[Anomaly] = []
    anomaly_response_items: List[Dict[str, Any]] = []
    for anomaly_data in detected_anomalies:
        event_index = anomaly_data.get("event_index")
        if event_index is None or event_index >= len(event_models):
            continue

        anomaly_type = anomaly_data.get("anomaly_type") or anomaly_data.get("type")
        if not anomaly_type:
            continue

        explanation = anomaly_data.get("description") or anomaly_data.get("explanation") or ""
        affected_lines = anomaly_data.get("affectedLines") or [event_index + 1]
        detection_method = anomaly_data.get("detectionMethod") or "rule_engine"

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

    anomaly_enrichment_inputs: List[Dict[str, Any]] = []
    for anomaly_index, item in enumerate(anomaly_response_items):
        row = int(item["event_row"])
        event = parsed_events[row - 1] if 0 < row <= len(parsed_events) else {}
        event_time = event.get("event_time")
        event_time_iso = event_time.isoformat() if event_time else None
        anomaly_enrichment_inputs.append(
            {
                "anomaly_index": anomaly_index,
                "severity": (item["anomaly"].severity or "").upper(),
                "anomalyType": item["anomaly"].anomaly_type,
                "entity": f"{event.get('username') or 'unknown_user'} / {event.get('source_ip') or 'unknown_ip'}",
                "destination": event.get("destination") or "unknown_destination",
                "bytesTransferred": int(event.get("bytes_transferred") or 0),
                "action": event.get("action") or "UNKNOWN",
                "category": event.get("category") or "Unknown",
                "timestamp": event_time_iso,
            }
        )

    enrichment_result = enrich_high_priority_anomalies(anomaly_enrichment_inputs)
    enrichment_by_index = enrichment_result.get("enriched_by_index", {})
    enrichment_status_by_index = enrichment_result.get("status_by_index", {})

    anomaly_payloads_for_ai: List[Dict[str, Any]] = []
    for item in anomaly_response_items:
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

    events_preview: List[Dict[str, Any]] = []
    for line_number, event in enumerate(parsed_events, start=1):
        event_time = event.get("event_time")
        events_preview.append(
            {
                "lineNumber": line_number,
                "event_time": event_time.isoformat() if event_time else None,
                "username": event.get("username"),
                "source_ip": event.get("source_ip"),
                "destination": event.get("destination"),
                "action": event.get("action"),
                "category": event.get("category"),
                "bytes_transferred": event.get("bytes_transferred"),
            }
        )

    anomaly_response_payload: List[Dict[str, Any]] = []
    for anomaly_index, item in enumerate(anomaly_response_items):
        severity_upper = (item["anomaly"].severity or "").upper()
        is_ai_eligible = severity_upper in {"HIGH", "CRITICAL"}
        payload: Dict[str, Any] = {
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
            "aiEnrichmentStatus": "eligible" if is_ai_eligible else "not_applicable",
        }

        status_value = enrichment_status_by_index.get(anomaly_index)
        if status_value:
            payload["aiEnrichmentStatus"] = status_value
            payload["aiEnrichmentReason"] = status_value.replace("_", " ")

        ai_enrichment = enrichment_by_index.get(anomaly_index)
        if ai_enrichment:
            payload["aiEnrichment"] = ai_enrichment
            payload["aiEnrichmentStatus"] = "enriched"
            payload["aiEnrichmentReason"] = "openai enrichment successful"

        anomaly_response_payload.append(payload)

    response_payload = {
        "upload_id": upload.id,
        "filename": upload.filename,
        "stored_file": stored_file,
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
        "anomalies": anomaly_response_payload,
    }

    _cleanup_file(upload, file_path)
    return response_payload


def build_persisted_analysis_payload(upload: Upload) -> Dict[str, Any]:
    events: List[Event] = sorted(upload.events, key=lambda item: item.id)
    anomalies: List[Anomaly] = sorted(upload.anomalies, key=lambda item: item.id)

    line_by_event_id = {
        event.id: index + 1
        for index, event in enumerate(events)
    }
    event_by_line = {
        index + 1: event
        for index, event in enumerate(events)
    }

    parsed_events: List[Dict[str, Any]] = []
    for event in events:
        parsed_events.append(
            {
                "event_time": event.event_time,
                "username": event.username,
                "source_ip": event.source_ip,
                "destination": event.destination,
                "action": event.action,
                "category": event.category,
                "bytes_transferred": int(event.bytes_transferred or 0),
                "raw_line": event.raw_line,
            }
        )

    metrics = generate_summary_metrics(parsed_events)
    summary: Summary | None = upload.summary
    if summary is None:
        summary_data = {
            "total_events": metrics["total_events"],
            "total_anomalies": len(anomalies),
            "blocked_events": metrics["blocked_events"],
            "allowed_events": metrics["allowed_events"],
            "unique_ips": metrics["unique_ips"],
            "top_categories": metrics["top_categories"],
            "top_destinations": metrics["top_destinations"],
            "top_source_ips": metrics["top_source_ips"],
        }
    else:
        summary_data = {
            "total_events": summary.total_events,
            "total_anomalies": summary.total_anomalies,
            "blocked_events": summary.blocked_count,
            "allowed_events": summary.allowed_count,
            "unique_ips": summary.unique_source_ips,
            "top_categories": summary.top_categories,
            "top_destinations": summary.top_destinations,
            "top_source_ips": summary.top_source_ips,
        }

    anomaly_response_items: List[Dict[str, Any]] = []
    for anomaly in anomalies:
        line_number = line_by_event_id.get(anomaly.event_id, 0)
        anomaly_response_items.append(
            {
                "anomaly": anomaly,
                "event_row": line_number,
                "affected_lines": [line_number] if line_number > 0 else [],
                "detection_method": "db_persisted",
            }
        )

    anomaly_enrichment_inputs: List[Dict[str, Any]] = []
    for anomaly_index, item in enumerate(anomaly_response_items):
        row = int(item["event_row"])
        event_model = event_by_line.get(row)
        anomaly_enrichment_inputs.append(
            {
                "anomaly_index": anomaly_index,
                "severity": (item["anomaly"].severity or "").upper(),
                "anomalyType": item["anomaly"].anomaly_type,
                "entity": (
                    f"{event_model.username or 'unknown_user'} / "
                    f"{event_model.source_ip or 'unknown_ip'}"
                    if event_model
                    else "unknown_user / unknown_ip"
                ),
                "destination": event_model.destination if event_model else "unknown_destination",
                "bytesTransferred": int(event_model.bytes_transferred or 0) if event_model else 0,
                "action": event_model.action if event_model and event_model.action else "UNKNOWN",
                "category": event_model.category if event_model and event_model.category else "Unknown",
                "timestamp": event_model.event_time.isoformat()
                if event_model and event_model.event_time
                else None,
            }
        )

    enrichment_result = enrich_high_priority_anomalies(anomaly_enrichment_inputs)
    enrichment_by_index = enrichment_result.get("enriched_by_index", {})
    enrichment_status_by_index = enrichment_result.get("status_by_index", {})

    anomaly_payloads_for_ai: List[Dict[str, Any]] = []
    for item in anomaly_response_items:
        row = int(item["event_row"])
        event_model = event_by_line.get(row)
        username = event_model.username if event_model and event_model.username else "unknown_user"
        source_ip = event_model.source_ip if event_model and event_model.source_ip else "unknown_ip"
        destination = (
            event_model.destination if event_model and event_model.destination else "unknown_destination"
        )
        bytes_transferred = int(event_model.bytes_transferred or 0) if event_model else 0
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
        summary_data,
        anomaly_payloads_for_ai,
        blocked_events_for_ai,
    )
    detection_notes = ["Historical analysis loaded from persisted database records."]
    detection_notes_summary = generate_detection_notes_summary(
        detection_notes,
        anomaly_payloads_for_ai,
    )

    events_preview: List[Dict[str, Any]] = []
    for line_number, event in enumerate(events, start=1):
        events_preview.append(
            {
                "lineNumber": line_number,
                "event_time": event.event_time.isoformat() if event.event_time else None,
                "username": event.username,
                "source_ip": event.source_ip,
                "destination": event.destination,
                "action": event.action,
                "category": event.category,
                "bytes_transferred": int(event.bytes_transferred or 0),
            }
        )

    anomaly_response_payload: List[Dict[str, Any]] = []
    for anomaly_index, item in enumerate(anomaly_response_items):
        severity_upper = (item["anomaly"].severity or "").upper()
        is_ai_eligible = severity_upper in {"HIGH", "CRITICAL"}
        payload: Dict[str, Any] = {
            "event_row": item["event_row"],
            "affectedLines": item["affected_lines"],
            "detectionMethod": item["detection_method"],
            "type": item["anomaly"].anomaly_type,
            "event_id": item["anomaly"].event_id,
            "anomaly_type": item["anomaly"].anomaly_type,
            "severity": item["anomaly"].severity,
            "confidence": float(item["anomaly"].score or 0),
            "explanation": item["anomaly"].description,
            "description": item["anomaly"].description,
            "aiEnrichmentStatus": "eligible" if is_ai_eligible else "not_applicable",
        }
        status_value = enrichment_status_by_index.get(anomaly_index)
        if status_value:
            payload["aiEnrichmentStatus"] = status_value
            payload["aiEnrichmentReason"] = status_value.replace("_", " ")
        ai_enrichment = enrichment_by_index.get(anomaly_index)
        if ai_enrichment:
            payload["aiEnrichment"] = ai_enrichment
            payload["aiEnrichmentStatus"] = "enriched"
            payload["aiEnrichmentReason"] = "openai enrichment successful"
        anomaly_response_payload.append(payload)

    return {
        "upload_id": upload.id,
        "filename": upload.filename,
        "stored_file": os.path.basename(upload.file_path or ""),
        "status": upload.status,
        "events_saved": len(events),
        "anomalies_detected": len(anomalies),
        "parse_errors_count": 0,
        "parse_errors": [],
        "detection_notes": detection_notes,
        "detection_notes_summary": detection_notes_summary,
        "events_preview": events_preview,
        "summary": summary_data,
        "ai_summary": executive_summary,
        "anomalies": anomaly_response_payload,
    }
