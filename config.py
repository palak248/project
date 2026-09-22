import os
import secrets
from datetime import timedelta


def _read_port():
    value = os.getenv("MYSQL_PORT", "3306")
    try:
        return int(value)
    except ValueError as error:
        raise ValueError("MYSQL_PORT must be an integer") from error


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30"))
    )

    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = _read_port()
    MYSQL_USER = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "")

    MYSQL_CONFIGURED = all(
        (
            MYSQL_USER,
            MYSQL_DATABASE,
        )
    )