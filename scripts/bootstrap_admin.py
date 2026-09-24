#!/usr/bin/env python3
"""Idempotently create the development bootstrap administrator.

This is intended only for a local development database. It never resets or
deletes data and stores only a password hash.
"""

import os

import mysql.connector
from werkzeug.security import generate_password_hash


LOGIN_IDENTIFIER = "Adarsh"
PASSWORD = "Adarsh248"


def main():
    required = ("MYSQL_USER", "MYSQL_DATABASE")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing database configuration: " + ", ".join(missing))

    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.environ["MYSQL_DATABASE"],
    )
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT user_id, role, login_identifier
            FROM users
            WHERE role = 'admin' OR login_identifier = %s
            ORDER BY role = 'admin' DESC
            LIMIT 1
            """,
            (LOGIN_IDENTIFIER,),
        )
        existing = cursor.fetchone()
        if existing is not None:
            if existing[1] == "admin":
                print("An administrator already exists; bootstrap made no changes.")
            else:
                raise RuntimeError(
                    f"Login identifier already belongs to a non-admin account: {LOGIN_IDENTIFIER}"
                )
            return
        cursor.execute(
            """
            INSERT INTO users (login_identifier, password_hash, role)
            VALUES (%s, %s, 'admin')
            """,
            (LOGIN_IDENTIFIER, generate_password_hash(PASSWORD)),
        )
        connection.commit()
        print(f"Bootstrap administrator created: {LOGIN_IDENTIFIER}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()