from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import select

from app import db
from app.models import User
from app.utils.security import hash_password, verify_password

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
ALLOWED_ROLES = {"SOC Analyst", "Security Admin", "Threat Hunter", "IR Analyst"}
DEMO_USERNAME = "analyst"
DEMO_PASSWORD = "analyst123"
DEMO_NAME = "Demo Analyst"
DEMO_ROLE = "SOC Analyst"


def _user_payload(user: User) -> dict:
    return {
        "id": user.public_id,
        "username": user.username,
        "role": user.role,
        "name": user.full_name,
    }


def _token_payload(user: User, status_code: int = 200):
    token = create_access_token(identity=user.public_id)
    return (
        jsonify(
            {
                "token": token,
                "access_token": token,
                "user": _user_payload(user),
            }
        ),
        status_code,
    )


def _build_synthetic_email(username: str) -> str:
    return f"{username}@local.user"


def _ensure_demo_user() -> None:
    existing = db.session.scalar(select(User).where(User.username == DEMO_USERNAME))
    if existing:
        return

    demo_user = User(
        username=DEMO_USERNAME,
        full_name=DEMO_NAME,
        email=_build_synthetic_email(DEMO_USERNAME),
        password_hash=hash_password(DEMO_PASSWORD),
        role=DEMO_ROLE,
    )
    db.session.add(demo_user)
    db.session.commit()


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    username = (payload.get("username") or "").strip().lower()
    password = payload.get("password") or ""
    role = (payload.get("role") or "").strip()

    if not name or not username or not password or not role:
        return jsonify({"error": "name, username, password, and role are required"}), 400
    if len(username) < 3:
        return jsonify({"error": "username must be at least 3 characters"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
    if role not in ALLOWED_ROLES:
        return jsonify({"error": "invalid role"}), 400

    existing_user = db.session.scalar(select(User).where(User.username == username))
    if existing_user:
        return jsonify({"error": "Username already taken"}), 409

    user = User(
        username=username,
        full_name=name,
        email=_build_synthetic_email(username),
        password_hash=hash_password(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()

    return _token_payload(user, status_code=201)


@auth_bp.post("/login")
def login():
    _ensure_demo_user()

    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip().lower()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = db.session.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "invalid credentials"}), 401

    return _token_payload(user, status_code=200)


@auth_bp.get("/me")
@jwt_required()
def me():
    user_identity = str(get_jwt_identity())
    user = db.session.scalar(select(User).where(User.public_id == user_identity))
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify(_user_payload(user)), 200
