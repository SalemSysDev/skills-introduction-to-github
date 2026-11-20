"""Application configuration.

All secrets and environment-specific values are read from environment
variables (or a local `.env` file). Nothing sensitive is hard-coded here.
"""
import os
import secrets
import warnings

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    APP_ENV = os.environ.get("APP_ENV", "development")

    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "dev.sqlite"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # Sessions / cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = int(os.environ.get("SESSION_LIFETIME_MINUTES", "120")) * 60

    # CSRF
    WTF_CSRF_TIME_LIMIT = None  # token valid for the whole session

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "25")) * 1024 * 1024
    MAX_IMAGE_MB = int(os.environ.get("MAX_IMAGE_MB", "8"))

    # Site
    DEFAULT_LANG = os.environ.get("DEFAULT_LANG", "ar")
    SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
    ADMIN_URL_PREFIX = "/" + os.environ.get("ADMIN_URL_PREFIX", "admin").strip("/")

    # Login protection
    LOGIN_MAX_ATTEMPTS = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_LOCK_MINUTES = int(os.environ.get("LOGIN_LOCK_MINUTES", "15"))

    # Contact form protection
    CONTACT_MAX_PER_HOUR = int(os.environ.get("CONTACT_MAX_PER_HOUR", "5"))

    # Optional e-mail notification for new messages
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = _bool("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_SENDER = os.environ.get("MAIL_SENDER")
    MAIL_NOTIFY_TO = os.environ.get("MAIL_NOTIFY_TO")

    # Trust X-Forwarded-* headers (set to 1 when running behind a reverse proxy)
    PROXY_FIX = _bool("PROXY_FIX", False)

    @classmethod
    def validate(cls, config: dict) -> None:
        if not config.get("SECRET_KEY"):
            if config.get("APP_ENV") == "production":
                raise RuntimeError("SECRET_KEY must be set in production (see .env.example).")
            warnings.warn(
                "SECRET_KEY is not set; using a temporary random key. "
                "Sessions will be lost on restart. Set SECRET_KEY in .env.",
                stacklevel=2,
            )
            config["SECRET_KEY"] = secrets.token_hex(32)


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
