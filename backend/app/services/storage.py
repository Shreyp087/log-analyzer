import os
from datetime import datetime
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def build_storage_filename(original_filename: str, upload_id: int) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    safe_name = secure_filename(original_filename or "upload.log") or "upload.log"
    unique_suffix = uuid4().hex[:10]
    return f"upload_{upload_id}_{timestamp}_{unique_suffix}_{safe_name}"


def save_upload_file(file_obj: FileStorage, upload_dir: str, upload_id: int) -> str:
    os.makedirs(upload_dir, exist_ok=True)
    storage_filename = build_storage_filename(file_obj.filename or "upload.log", upload_id)
    absolute_path = os.path.abspath(os.path.join(upload_dir, storage_filename))
    file_obj.save(absolute_path)
    return absolute_path
