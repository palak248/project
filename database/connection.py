import mysql.connector
from flask import current_app


def get_db_connection():
    """Create a MySQL connection using the current application configuration."""
    required_values = {
        "MYSQL_USER": current_app.config["MYSQL_USER"],
        "MYSQL_DATABASE": current_app.config["MYSQL_DATABASE"],
    }
    missing_values = [name for name, value in required_values.items() if not value]
    if missing_values:
        names = ", ".join(missing_values)
        raise RuntimeError(f"Missing database configuration: {names}")

    return mysql.connector.connect(
        host=current_app.config["MYSQL_HOST"],
        port=current_app.config["MYSQL_PORT"],
        user=current_app.config["MYSQL_USER"],
        password=current_app.config["MYSQL_PASSWORD"],
        database=current_app.config["MYSQL_DATABASE"],
    )