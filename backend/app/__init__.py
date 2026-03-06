import os
from typing import Optional

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import get_config

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(config_name: Optional[str] = None) -> Flask:
    app = Flask(__name__)
    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(get_config(env_name))

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from routes import register_routes

    register_routes(app)
    return app
