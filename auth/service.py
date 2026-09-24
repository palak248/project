from contextlib import contextmanager
import hmac
import secrets

from flask import session
from werkzeug.security import check_password_hash, generate_password_hash

from admin import repository as admin_repository
from admin.service import validate_student_form
from database.connection import get_db_connection


class ValidationError(ValueError):
    pass


class AuthenticationError(ValueError):
    pass


class SetupUnavailable(ValueError):
    pass


def csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def valid_csrf_token(token):
    expected = session.get("csrf_token")
    return bool(token and expected and hmac.compare_digest(token, expected))


@contextmanager
def _transaction():
    connection = get_db_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _required_text(value, label, maximum):
    value = value.strip()
    if not value:
        raise ValidationError(f"{label} is required.")
    if len(value) > maximum:
        raise ValidationError(f"{label} must be {maximum} characters or fewer.")
    return value


def _new_password(form):
    password = form.get("password", "")
    confirmation = form.get("password_confirmation", "")
    if len(password) < 8:
        raise ValidationError("Password must contain at least 8 characters.")
    if password != confirmation:
        raise ValidationError("New passwords do not match.")
    return password


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


def get_active_user_role(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT role
            FROM users
            WHERE user_id = %s AND is_active = TRUE
            LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()
        connection.close()


def first_admin_setup_available():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        return cursor.fetchone()[0] == 0
    finally:
        cursor.close()
        connection.close()


def create_first_admin(form):
    login_identifier = _required_text(form.get("login_identifier", ""), "Login identifier", 100)
    password = _new_password(form)

    connection = get_db_connection()
    cursor = connection.cursor()
    lock_name = "student_performance_first_admin"
    lock_acquired = False
    try:
        cursor.execute("SELECT GET_LOCK(%s, 10)", (lock_name,))
        lock_acquired = cursor.fetchone()[0] == 1
        if not lock_acquired:
            raise RuntimeError("Could not acquire first administrator setup lock")

        cursor.execute("SELECT user_id FROM users WHERE role = 'admin' LIMIT 1")
        if cursor.fetchone() is not None:
            raise SetupUnavailable("First administrator setup is closed.")

        cursor.execute(
            """
            INSERT INTO users (login_identifier, password_hash, role)
            VALUES (%s, %s, 'admin')
            """,
            (login_identifier, generate_password_hash(password)),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if lock_acquired:
            cursor.execute("SELECT RELEASE_LOCK(%s)", (lock_name,))
        cursor.close()
        connection.close()


def change_password(user_id, current_password, form):
    new_password = _new_password(form)
    with _transaction() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT password_hash
                FROM users
                WHERE user_id = %s AND is_active = TRUE
                FOR UPDATE
                """,
                (user_id,),
            )
            user = cursor.fetchone()
            if user is None or not _password_matches(user["password_hash"], current_password):
                raise AuthenticationError("Current password is incorrect.")

            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                (generate_password_hash(new_password), user_id),
            )
        finally:
            cursor.close()


def register_student(form):
    student_number, full_name, identifier, password = validate_student_form(form, True)
    with _transaction() as connection:
        return admin_repository.create_student(
            connection,
            student_number,
            full_name,
            identifier,
            generate_password_hash(password),
        )


def _password_matches(password_hash, password):
    try:
        return check_password_hash(password_hash, password)
    except (TypeError, ValueError):
        return False


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