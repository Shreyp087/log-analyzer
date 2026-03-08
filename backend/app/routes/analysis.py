from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app import db
from app.models import Upload, User
from app.services.analysis_pipeline import (
    build_persisted_analysis_payload,
    process_upload_analysis,
)

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


def _resolve_current_user():
    user_identity = str(get_jwt_identity() or "").strip()
    user = db.session.scalar(select(User).where(User.public_id == user_identity))
    if user is None and user_identity.isdigit():
        user = db.session.get(User, int(user_identity))
    return user


@analysis_bp.post("")
@jwt_required()
def run_analysis():
    payload = request.get_json(silent=True) or {}
    upload_id = payload.get("upload_id", payload.get("fileId"))

    if upload_id in (None, ""):
        return jsonify({"error": "upload_id is required"}), 400

    try:
        upload_id = int(upload_id)
    except (TypeError, ValueError):
        return jsonify({"error": "upload_id must be an integer"}), 400

    user = _resolve_current_user()
    if user is None:
        return jsonify({"error": "user not found"}), 404

    upload = db.session.scalar(
        select(Upload).where(Upload.id == upload_id, Upload.user_id == user.id)
    )
    if upload is None:
        return jsonify({"error": "upload not found"}), 404

    try:
        if upload.file_path:
            result = process_upload_analysis(upload)
        else:
            result = build_persisted_analysis_payload(upload)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "failed to process upload", "details": str(exc)}), 500

    return jsonify(result), 200


@analysis_bp.get("/<int:upload_id>")
@jwt_required()
def get_analysis(upload_id: int):
    user = _resolve_current_user()
    if user is None:
        return jsonify({"error": "user not found"}), 404

    upload = db.session.scalar(
        select(Upload).where(Upload.id == upload_id, Upload.user_id == user.id)
    )
    if upload is None:
        return jsonify({"error": "upload not found"}), 404

    if upload.status in {"uploaded", "queued"}:
        return jsonify({"error": "upload exists but has not been analyzed yet"}), 409

    try:
        result = build_persisted_analysis_payload(upload)
    except Exception as exc:
        return jsonify({"error": "failed to load analysis", "details": str(exc)}), 500

    return jsonify(result), 200
