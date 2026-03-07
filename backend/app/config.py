import os

from dotenv import load_dotenv

load_dotenv()

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me-at-least-32")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-me-at-least-32")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://log_user:log_password@localhost:5432/log_analyzer",
    )
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BACKEND_ROOT, "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(20 * 1024 * 1024)))


class DevelopmentConfig(BaseConfig):
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(BaseConfig):
    DEBUG = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(config_name: str):
    return CONFIG_MAP.get(config_name, DevelopmentConfig)
