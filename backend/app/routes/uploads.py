import os
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app import db
from app.models import Upload, User
from app.services.storage import save_upload_file

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api/uploads")

ALLOWED_EXTENSIONS = {".log", ".txt", ".csv"}
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/csv",
    "application/csv",
    "application/octet-stream",
    "application/vnd.ms-excel",
}


def _resolve_current_user() -> Optional[User]:
    user_identity = str(get_jwt_identity() or "").strip()
    user = db.session.scalar(select(User).where(User.public_id == user_identity))
    if user is None and user_identity.isdigit():
        user = db.session.get(User, int(user_identity))
    return user


def _allowed_file_extension(filename: str) -> bool:
    extension = os.path.splitext(filename or "")[1].lower()
    return extension in ALLOWED_EXTENSIONS


def _is_supported_file(file_obj) -> bool:
    if not file_obj or not file_obj.filename:
        return False
    if not _allowed_file_extension(file_obj.filename):
        return False
    # Some browsers/dev tools omit MIME type, so extension remains the source of truth.
    return not file_obj.mimetype or file_obj.mimetype in ALLOWED_MIME_TYPES


def _read_file_size(file_obj) -> Optional[int]:
    stream = getattr(file_obj, "stream", None)
    if stream is None or not hasattr(stream, "tell") or not hasattr(stream, "seek"):
        return None

    current_pos = stream.tell()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(current_pos, os.SEEK_SET)
    return int(size)


@uploads_bp.post("")
@jwt_required()
def create_upload():
    file_obj = request.files.get("file")
    if file_obj is None or not file_obj.filename:
        return jsonify({"error": "file is required"}), 400

    if not _is_supported_file(file_obj):
        return (
            jsonify(
                {
                    "error": "unsupported file type; allowed extensions: .log, .txt, .csv",
                }
            ),
            400,
        )

    size = _read_file_size(file_obj)
    max_size = int(current_app.config.get("MAX_CONTENT_LENGTH") or 0)
    if size is not None and max_size > 0 and size > max_size:
        return jsonify({"error": "uploaded file exceeds maximum allowed size"}), 413

    source = (request.form.get("source") or "zscaler").strip().lower()
    if source != "zscaler":
        return jsonify({"error": "only zscaler source is supported in this stage"}), 400

    user = _resolve_current_user()
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

        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "failed to store upload", "details": str(exc)}), 500

    return (
        jsonify(
            {
                "upload_id": upload.id,
                "filename": upload.filename,
                "stored_file": os.path.basename(upload.file_path or ""),
                "status": upload.status,
            }
        ),
        201,
    )
