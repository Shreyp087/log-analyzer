from datetime import datetime
from uuid import uuid4

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(
        db.String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid4())
    )
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="SOC Analyst")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    uploads = db.relationship(
        "Upload", back_populates="user", lazy="select", cascade="all, delete-orphan"
    )


class Upload(db.Model):
    __tablename__ = "uploads"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    source = db.Column(db.String(100), nullable=False, default="zscaler")
    status = db.Column(db.String(50), nullable=False, default="uploaded")
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="uploads")
    events = db.relationship(
        "Event", back_populates="upload", lazy="select", cascade="all, delete-orphan"
    )
    anomalies = db.relationship(
        "Anomaly",
        back_populates="upload",
        lazy="select",
        cascade="all, delete-orphan",
    )
    summary = db.relationship(
        "Summary", back_populates="upload", uselist=False, cascade="all, delete-orphan"
    )


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(
        db.Integer, db.ForeignKey("uploads.id"), nullable=False, index=True
    )
    event_time = db.Column(db.DateTime, nullable=True, index=True)
    username = db.Column(db.String(255), nullable=True, index=True)
    source_ip = db.Column(db.String(45), nullable=True, index=True)
    destination = db.Column(db.String(500), nullable=True)
    action = db.Column(db.String(50), nullable=True, index=True)
    category = db.Column(db.String(100), nullable=True)
    bytes_transferred = db.Column(db.BigInteger, nullable=True)
    raw_line = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    upload = db.relationship("Upload", back_populates="events")
    anomalies = db.relationship(
        "Anomaly", back_populates="event", lazy="select", cascade="all, delete-orphan"
    )


class Anomaly(db.Model):
    __tablename__ = "anomalies"

    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(
        db.Integer, db.ForeignKey("uploads.id"), nullable=False, index=True
    )
    event_id = db.Column(
        db.Integer, db.ForeignKey("events.id"), nullable=False, index=True
    )
    anomaly_type = db.Column(db.String(100), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, default="medium")
    score = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=False)
    detected_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, nullable=False, default=False)

    upload = db.relationship("Upload", back_populates="anomalies")
    event = db.relationship("Event", back_populates="anomalies")


class Summary(db.Model):
    __tablename__ = "summaries"

    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(
        db.Integer, db.ForeignKey("uploads.id"), nullable=False, unique=True, index=True
    )
    total_events = db.Column(db.Integer, nullable=False, default=0)
    total_anomalies = db.Column(db.Integer, nullable=False, default=0)
    allowed_count = db.Column(db.Integer, nullable=False, default=0)
    blocked_count = db.Column(db.Integer, nullable=False, default=0)
    unique_source_ips = db.Column(db.Integer, nullable=False, default=0)
    top_categories = db.Column(db.JSON, nullable=False, default=list)
    top_destinations = db.Column(db.JSON, nullable=False, default=list)
    top_source_ips = db.Column(db.JSON, nullable=False, default=list)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    upload = db.relationship("Upload", back_populates="summary")
