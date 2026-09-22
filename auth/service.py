from werkzeug.security import check_password_hash

from database.connection import get_db_connection


def authenticate_user(login_identifier, password):
    user = _find_active_user(login_identifier)
    if user is None:
        return None

    try:
        password_matches = check_password_hash(user["password_hash"], password)
    except (TypeError, ValueError):
        password_matches = False

    if not password_matches:
        return None

    return {
        "user_id": user["user_id"],
        "role": user["role"],
    }


def _find_active_user(login_identifier):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT user_id, password_hash, role
            FROM users
            WHERE login_identifier = %s AND is_active = TRUE
            LIMIT 1
            """,
            (login_identifier,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()