from flask import Flask

from app.routes.auth import auth_bp
from app.routes.uploads import uploads_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(uploads_bp)
