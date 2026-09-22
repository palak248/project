from contextlib import contextmanager

from database.connection import get_db_connection


@contextmanager
def transaction():
    connection = get_db_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _fetch_all(query, parameters=()):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, parameters)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def _fetch_one(query, parameters=()):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, parameters)
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def dashboard_counts():
    row = _fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM students) AS student_count,
            (SELECT COUNT(*) FROM teachers) AS teacher_count,
            (SELECT COUNT(*) FROM classes) AS class_count,
            (SELECT COUNT(*) FROM subjects) AS subject_count,
            (SELECT COUNT(*) FROM teacher_class_subjects) AS assignment_count
        """
    )
    return row


def list_students(search="", status="all"):
    conditions = []
    parameters = []
    if search:
        conditions.append("(s.full_name LIKE %s OR s.student_number LIKE %s)")
        search_value = f"%{search}%"
        parameters.extend((search_value, search_value))
    if status == "active":
        conditions.append("u.is_active = TRUE")
    elif status == "inactive":
        conditions.append("u.is_active = FALSE")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return _fetch_all(
        f"""
        SELECT s.student_id, s.student_number, s.full_name,
               u.user_id, u.login_identifier, u.is_active
        FROM students AS s
        JOIN users AS u ON u.user_id = s.user_id
        {where_clause}
        ORDER BY s.full_name, s.student_number
        """,
        parameters,
    )


def get_student(student_id):
    return _fetch_one(
        """
        SELECT s.student_id, s.student_number, s.full_name,
               u.user_id, u.login_identifier, u.is_active
        FROM students AS s
        JOIN users AS u ON u.user_id = s.user_id
        WHERE s.student_id = %s
        """,
        (student_id,),
    )


def create_student(connection, student_number, full_name, login_identifier, password_hash):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (login_identifier, password_hash, role)
            VALUES (%s, %s, 'student')
            """,
            (login_identifier, password_hash),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO students (user_id, student_number, full_name)
            VALUES (%s, %s, %s)
            """,
            (user_id, student_number, full_name),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def update_student(connection, student_id, student_number, full_name, login_identifier):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE students AS s
            JOIN users AS u ON u.user_id = s.user_id
            SET s.student_number = %s,
                s.full_name = %s,
                u.login_identifier = %s
            WHERE s.student_id = %s
            """,
            (student_number, full_name, login_identifier, student_id),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def deactivate_student(connection, student_id):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE users AS u
            JOIN students AS s ON s.user_id = u.user_id
            SET u.is_active = FALSE
            WHERE s.student_id = %s
            """,
            (student_id,),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def list_teachers(search="", status="all"):
    conditions = []
    parameters = []
    if search:
        conditions.append("(t.full_name LIKE %s OR t.teacher_number LIKE %s)")
        search_value = f"%{search}%"
        parameters.extend((search_value, search_value))
    if status == "active":
        conditions.append("u.is_active = TRUE")
    elif status == "inactive":
        conditions.append("u.is_active = FALSE")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return _fetch_all(
        f"""
        SELECT t.teacher_id, t.teacher_number, t.full_name,
               u.user_id, u.login_identifier, u.is_active
        FROM teachers AS t
        JOIN users AS u ON u.user_id = t.user_id
        {where_clause}
        ORDER BY t.full_name, t.teacher_number
        """,
        parameters,
    )


def get_teacher(teacher_id):
    return _fetch_one(
        """
        SELECT t.teacher_id, t.teacher_number, t.full_name,
               u.user_id, u.login_identifier, u.is_active
        FROM teachers AS t
        JOIN users AS u ON u.user_id = t.user_id
        WHERE t.teacher_id = %s
        """,
        (teacher_id,),
    )


def create_teacher(connection, teacher_number, full_name, login_identifier, password_hash):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (login_identifier, password_hash, role)
            VALUES (%s, %s, 'teacher')
            """,
            (login_identifier, password_hash),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO teachers (user_id, teacher_number, full_name)
            VALUES (%s, %s, %s)
            """,
            (user_id, teacher_number, full_name),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def update_teacher(connection, teacher_id, teacher_number, full_name, login_identifier):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE teachers AS t
            JOIN users AS u ON u.user_id = t.user_id
            SET t.teacher_number = %s,
                t.full_name = %s,
                u.login_identifier = %s
            WHERE t.teacher_id = %s
            """,
            (teacher_number, full_name, login_identifier, teacher_id),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def deactivate_teacher(connection, teacher_id):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE users AS u
            JOIN teachers AS t ON t.user_id = u.user_id
            SET u.is_active = FALSE
            WHERE t.teacher_id = %s
            """,
            (teacher_id,),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def list_classes(search=""):
    parameters = []
    where_clause = ""
    if search:
        where_clause = "WHERE class_name LIKE %s OR academic_year LIKE %s"
        search_value = f"%{search}%"
        parameters.extend((search_value, search_value))
    return _fetch_all(
        f"""
        SELECT class_id, class_name, academic_year, created_at
        FROM classes
        {where_clause}
        ORDER BY academic_year DESC, class_name
        """,
        parameters,
    )


def get_class(class_id):
    return _fetch_one(
        "SELECT class_id, class_name, academic_year FROM classes WHERE class_id = %s",
        (class_id,),
    )


def create_class(connection, class_name, academic_year):
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO classes (class_name, academic_year) VALUES (%s, %s)",
            (class_name, academic_year),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def update_class(connection, class_id, class_name, academic_year):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE classes
            SET class_name = %s, academic_year = %s
            WHERE class_id = %s
            """,
            (class_name, academic_year, class_id),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def delete_class(connection, class_id):
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM classes WHERE class_id = %s", (class_id,))
        return cursor.rowcount
    finally:
        cursor.close()


def list_subjects(search=""):
    parameters = []
    where_clause = ""
    if search:
        where_clause = "WHERE subject_code LIKE %s OR subject_name LIKE %s"
        search_value = f"%{search}%"
        parameters.extend((search_value, search_value))
    return _fetch_all(
        f"""
        SELECT subject_id, subject_code, subject_name, created_at
        FROM subjects
        {where_clause}
        ORDER BY subject_name, subject_code
        """,
        parameters,
    )


def get_subject(subject_id):
    return _fetch_one(
        "SELECT subject_id, subject_code, subject_name FROM subjects WHERE subject_id = %s",
        (subject_id,),
    )


def create_subject(connection, subject_code, subject_name):
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO subjects (subject_code, subject_name) VALUES (%s, %s)",
            (subject_code, subject_name),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def update_subject(connection, subject_id, subject_code, subject_name):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE subjects
            SET subject_code = %s, subject_name = %s
            WHERE subject_id = %s
            """,
            (subject_code, subject_name, subject_id),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def delete_subject(connection, subject_id):
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
        return cursor.rowcount
    finally:
        cursor.close()


def assignment_options():
    return {
        "teachers": _fetch_all(
            """
            SELECT t.teacher_id, t.full_name, t.teacher_number
            FROM teachers AS t
            JOIN users AS u ON u.user_id = t.user_id
            WHERE u.is_active = TRUE
            ORDER BY t.full_name
            """
        ),
        "classes": _fetch_all(
            "SELECT class_id, class_name, academic_year FROM classes ORDER BY academic_year DESC, class_name"
        ),
        "subjects": _fetch_all(
            "SELECT subject_id, subject_code, subject_name FROM subjects ORDER BY subject_name"
        ),
    }


def list_assignments():
    return _fetch_all(
        """
        SELECT tcs.assignment_id,
               t.full_name AS teacher_name,
               t.teacher_number,
               c.class_name,
               c.academic_year,
               s.subject_code,
               s.subject_name
        FROM teacher_class_subjects AS tcs
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        JOIN classes AS c ON c.class_id = cs.class_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        ORDER BY c.academic_year DESC, c.class_name, s.subject_name, t.full_name
        """
    )


def create_assignment(connection, teacher_id, class_id, subject_id):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT class_subject_id
            FROM class_subjects
            WHERE class_id = %s AND subject_id = %s
            FOR UPDATE
            """,
            (class_id, subject_id),
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                """
                INSERT INTO class_subjects (class_id, subject_id)
                VALUES (%s, %s)
                """,
                (class_id, subject_id),
            )
            class_subject_id = cursor.lastrowid
        else:
            class_subject_id = row[0]

        cursor.execute(
            """
            INSERT INTO teacher_class_subjects (teacher_id, class_subject_id)
            VALUES (%s, %s)
            """,
            (teacher_id, class_subject_id),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def delete_assignment(connection, assignment_id):
    cursor = connection.cursor()
    try:
        cursor.execute(
            "DELETE FROM teacher_class_subjects WHERE assignment_id = %s",
            (assignment_id,),
        )
        return cursor.rowcount
    finally:
        cursor.close()