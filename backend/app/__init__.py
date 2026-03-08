import os
from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import RequestEntityTooLarge

from app.config import get_config

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(config_name: Optional[str] = None) -> Flask:
    app = Flask(__name__)
    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(get_config(env_name))
    CORS(
        app,
        resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", [])}},
        supports_credentials=False,
    )

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    @jwt.unauthorized_loader
    def _handle_missing_token(reason: str):
        return (
            jsonify(
                {
                    "error": "authorization token is required",
                    "code": "auth_missing_token",
                    "details": reason,
                }
            ),
            401,
        )

    @jwt.invalid_token_loader
    def _handle_invalid_token(reason: str):
        return (
            jsonify(
                {
                    "error": "invalid authorization token",
                    "code": "auth_invalid_token",
                    "details": reason,
                }
            ),
            401,
        )

    @jwt.expired_token_loader
    def _handle_expired_token(_jwt_header, _jwt_payload):
        return (
            jsonify(
                {
                    "error": "authorization token has expired",
                    "code": "auth_token_expired",
                }
            ),
            401,
        )

    @app.errorhandler(RequestEntityTooLarge)
    def _handle_file_too_large(_err):
        return (
            jsonify(
                {
                    "error": "uploaded file exceeds maximum allowed size",
                    "code": "file_too_large",
                }
            ),
            413,
        )

    from app import models  # noqa: F401

    from app.routes import register_routes

    register_routes(app)
    return app
