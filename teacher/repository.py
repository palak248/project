from database.connection import get_db_connection


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


def get_profile(user_id):
    return _fetch_one(
        """
        SELECT t.teacher_id, t.teacher_number, t.full_name,
               u.login_identifier, u.is_active
        FROM teachers AS t
        JOIN users AS u ON u.user_id = t.user_id
        WHERE t.user_id = %s AND u.is_active = TRUE
        """,
        (user_id,),
    )


def get_dashboard_summary(user_id):
    return _fetch_one(
        """
        SELECT
            COUNT(DISTINCT tcs.assignment_id) AS assignment_count,
            COUNT(DISTINCT cs.class_id) AS class_count,
            COUNT(DISTINCT cs.subject_id) AS subject_count,
            COUNT(DISTINCT enrolled.student_id) AS student_count
        FROM teachers AS t
        JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
        LEFT JOIN teacher_class_subjects AS tcs ON tcs.teacher_id = t.teacher_id
        LEFT JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        LEFT JOIN class_students AS enrolled ON enrolled.class_id = cs.class_id
        WHERE t.user_id = %s
        """,
        (user_id,),
    )


def list_classes(user_id):
    return _fetch_all(
        """
        SELECT c.class_id, c.class_name, c.academic_year,
               COUNT(DISTINCT cs.subject_id) AS subject_count,
               COUNT(DISTINCT enrolled.student_id) AS student_count
        FROM teacher_class_subjects AS tcs
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
        JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        JOIN classes AS c ON c.class_id = cs.class_id
        LEFT JOIN class_students AS enrolled ON enrolled.class_id = c.class_id
        WHERE t.user_id = %s
        GROUP BY c.class_id, c.class_name, c.academic_year
        ORDER BY c.academic_year DESC, c.class_name
        """,
        (user_id,),
    )


def list_assignments(user_id):
    return _fetch_all(
        """
        SELECT cs.class_subject_id, c.class_id, c.class_name, c.academic_year,
               s.subject_id, s.subject_code, s.subject_name,
               COUNT(DISTINCT enrolled.student_id) AS student_count
        FROM teacher_class_subjects AS tcs
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
        JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        JOIN classes AS c ON c.class_id = cs.class_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        LEFT JOIN class_students AS enrolled ON enrolled.class_id = c.class_id
        WHERE t.user_id = %s
        GROUP BY cs.class_subject_id, c.class_id, c.class_name, c.academic_year,
                 s.subject_id, s.subject_code, s.subject_name
        ORDER BY c.academic_year DESC, c.class_name, s.subject_name
        """,
        (user_id,),
    )


def get_class_for_teacher(user_id, class_id):
    return _fetch_one(
        """
        SELECT DISTINCT c.class_id, c.class_name, c.academic_year
        FROM teacher_class_subjects AS tcs
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
        JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        JOIN classes AS c ON c.class_id = cs.class_id
        WHERE t.user_id = %s AND c.class_id = %s
        """,
        (user_id, class_id),
    )


def list_class_assignments(user_id, class_id):
    return _fetch_all(
        """
        SELECT cs.class_subject_id, s.subject_id, s.subject_code, s.subject_name
        FROM teacher_class_subjects AS tcs
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
        JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        WHERE t.user_id = %s AND cs.class_id = %s
        ORDER BY s.subject_name, s.subject_code
        """,
        (user_id, class_id),
    )


def list_class_students(user_id, class_id):
    return _fetch_all(
        """
        SELECT DISTINCT s.student_id, s.student_number, s.full_name, u.is_active
        FROM teacher_class_subjects AS tcs
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS teacher_user ON teacher_user.user_id = t.user_id
            AND teacher_user.is_active = TRUE
        JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        JOIN class_students AS enrolled ON enrolled.class_id = cs.class_id
        JOIN students AS s ON s.student_id = enrolled.student_id
        JOIN users AS u ON u.user_id = s.user_id
        WHERE t.user_id = %s AND cs.class_id = %s
        ORDER BY s.full_name, s.student_number
        """,
        (user_id, class_id),
    )


def get_subject_for_teacher(user_id, class_subject_id):
    return _fetch_one(
        """
        SELECT cs.class_subject_id, c.class_id, c.class_name, c.academic_year,
               s.subject_id, s.subject_code, s.subject_name
        FROM teacher_class_subjects AS tcs
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
        JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        JOIN classes AS c ON c.class_id = cs.class_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        WHERE t.user_id = %s AND cs.class_subject_id = %s
        LIMIT 1
        """,
        (user_id, class_subject_id),
    )


def list_subject_students(user_id, class_subject_id):
    return _fetch_all(
        """
        SELECT DISTINCT s.student_id, s.student_number, s.full_name, u.is_active
        FROM teacher_class_subjects AS tcs
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS teacher_user ON teacher_user.user_id = t.user_id
            AND teacher_user.is_active = TRUE
        JOIN class_subjects AS cs ON cs.class_subject_id = tcs.class_subject_id
        JOIN class_students AS enrolled ON enrolled.class_id = cs.class_id
        JOIN students AS s ON s.student_id = enrolled.student_id
        JOIN users AS u ON u.user_id = s.user_id
        WHERE t.user_id = %s AND cs.class_subject_id = %s
        ORDER BY s.full_name, s.student_number
        """,
        (user_id, class_subject_id),
    )


def list_attendance(user_id, class_subject_id=None, attendance_date=None):
    conditions = ["t.user_id = %s", "teacher_user.is_active = TRUE"]
    parameters = [user_id]
    if class_subject_id is not None:
        conditions.append("att.class_subject_id = %s")
        parameters.append(class_subject_id)
    if attendance_date is not None:
        conditions.append("att.attendance_date = %s")
        parameters.append(attendance_date)
    return _fetch_all(
        f"""
        SELECT att.attendance_id, att.class_subject_id, att.attendance_date, att.status,
               c.class_id, c.class_name, c.academic_year,
               s.subject_code, s.subject_name,
               st.student_id, st.student_number, st.full_name
        FROM attendance AS att
        JOIN class_subjects AS cs ON cs.class_subject_id = att.class_subject_id
        JOIN teacher_class_subjects AS tcs ON tcs.class_subject_id = cs.class_subject_id
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS teacher_user ON teacher_user.user_id = t.user_id
        JOIN classes AS c ON c.class_id = cs.class_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        JOIN students AS st ON st.student_id = att.student_id
        WHERE {' AND '.join(conditions)}
        ORDER BY att.attendance_date DESC, c.class_name, s.subject_name,
                 st.full_name, st.student_number
        """,
        parameters,
    )


def list_attendance_students(user_id, class_subject_id, attendance_date):
    return _fetch_all(
        """
        SELECT st.student_id, st.student_number, st.full_name, student_user.is_active,
               att.attendance_id, att.status
        FROM class_subjects AS cs
        JOIN teacher_class_subjects AS tcs ON tcs.class_subject_id = cs.class_subject_id
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS teacher_user ON teacher_user.user_id = t.user_id
            AND teacher_user.is_active = TRUE
        JOIN class_students AS enrolled ON enrolled.class_id = cs.class_id
        JOIN students AS st ON st.student_id = enrolled.student_id
        JOIN users AS student_user ON student_user.user_id = st.user_id
        LEFT JOIN attendance AS att
            ON att.class_subject_id = cs.class_subject_id
            AND att.student_id = st.student_id
            AND att.attendance_date = %s
        WHERE t.user_id = %s AND cs.class_subject_id = %s
        ORDER BY st.full_name, st.student_number
        """,
        (attendance_date, user_id, class_subject_id),
    )


def upsert_attendance(
    connection, user_id, class_subject_id, student_id, attendance_date, status
):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT cs.class_subject_id
            FROM class_subjects AS cs
            JOIN teacher_class_subjects AS tcs
                ON tcs.class_subject_id = cs.class_subject_id
            JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
            JOIN users AS teacher_user ON teacher_user.user_id = t.user_id
                AND teacher_user.is_active = TRUE
            JOIN class_students AS enrolled ON enrolled.class_id = cs.class_id
                AND enrolled.student_id = %s
            WHERE t.user_id = %s AND cs.class_subject_id = %s
            FOR UPDATE
            """,
            (student_id, user_id, class_subject_id),
        )
        if cursor.fetchone() is None:
            return 0
        cursor.execute(
            """
            INSERT INTO attendance
                (class_subject_id, student_id, attendance_date, status)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
            """,
            (class_subject_id, student_id, attendance_date, status),
        )
        return 1
    finally:
        cursor.close()


def list_assessments(user_id, class_subject_id=None):
    conditions = ["t.user_id = %s", "u.is_active = TRUE"]
    parameters = [user_id]
    if class_subject_id is not None:
        conditions.append("a.class_subject_id = %s")
        parameters.append(class_subject_id)
    return _fetch_all(
        f"""
        SELECT a.assessment_id, a.class_subject_id, a.assessment_type,
               a.title, a.assessment_date, a.max_marks,
               c.class_id, c.class_name, c.academic_year,
               s.subject_code, s.subject_name,
               COUNT(DISTINCT ar.assessment_result_id) AS result_count,
               COUNT(DISTINCT enrolled.student_id) AS student_count
        FROM assessments AS a
        JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
        JOIN teacher_class_subjects AS tcs ON tcs.class_subject_id = cs.class_subject_id
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS u ON u.user_id = t.user_id
        JOIN classes AS c ON c.class_id = cs.class_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        LEFT JOIN assessment_results AS ar ON ar.assessment_id = a.assessment_id
        LEFT JOIN class_students AS enrolled ON enrolled.class_id = c.class_id
        WHERE {' AND '.join(conditions)}
        GROUP BY a.assessment_id, a.class_subject_id, a.assessment_type,
                 a.title, a.assessment_date, a.max_marks,
                 c.class_id, c.class_name, c.academic_year,
                 s.subject_code, s.subject_name
        ORDER BY a.assessment_date DESC, c.class_name, s.subject_name, a.title
        """,
        parameters,
    )


def get_assessment_for_teacher(user_id, assessment_id):
    return _fetch_one(
        """
        SELECT a.assessment_id, a.class_subject_id, a.assessment_type,
               a.title, a.assessment_date, a.max_marks,
               c.class_id, c.class_name, c.academic_year,
               s.subject_code, s.subject_name
        FROM assessments AS a
        JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
        JOIN teacher_class_subjects AS tcs ON tcs.class_subject_id = cs.class_subject_id
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
        JOIN classes AS c ON c.class_id = cs.class_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        WHERE t.user_id = %s AND a.assessment_id = %s
        LIMIT 1
        """,
        (user_id, assessment_id),
    )


def list_assessment_students(user_id, assessment_id):
    return _fetch_all(
        """
        SELECT s.student_id, s.student_number, s.full_name, u.is_active,
               ar.assessment_result_id, ar.obtained_marks
        FROM assessments AS a
        JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
        JOIN teacher_class_subjects AS tcs ON tcs.class_subject_id = cs.class_subject_id
        JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
        JOIN users AS teacher_user ON teacher_user.user_id = t.user_id
            AND teacher_user.is_active = TRUE
        JOIN class_students AS enrolled ON enrolled.class_id = cs.class_id
        JOIN students AS s ON s.student_id = enrolled.student_id
        JOIN users AS u ON u.user_id = s.user_id
        LEFT JOIN assessment_results AS ar
            ON ar.assessment_id = a.assessment_id AND ar.student_id = s.student_id
        WHERE t.user_id = %s AND a.assessment_id = %s
        ORDER BY s.full_name, s.student_number
        """,
        (user_id, assessment_id),
    )


def create_assessment(
    connection,
    user_id,
    class_subject_id,
    assessment_type,
    title,
    assessment_date,
    max_marks,
):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT cs.class_subject_id
            FROM class_subjects AS cs
            JOIN teacher_class_subjects AS tcs
                ON tcs.class_subject_id = cs.class_subject_id
            JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
            JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
            WHERE t.user_id = %s AND cs.class_subject_id = %s
            FOR UPDATE
            """,
            (user_id, class_subject_id),
        )
        if cursor.fetchone() is None:
            return 0
        cursor.execute(
            """
            INSERT INTO assessments
                (class_subject_id, assessment_type, title, assessment_date, max_marks)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (class_subject_id, assessment_type, title, assessment_date, max_marks),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def update_assessment(
    connection,
    user_id,
    assessment_id,
    assessment_type,
    title,
    assessment_date,
    max_marks,
):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM assessment_results AS ar
                JOIN assessments AS existing
                    ON existing.assessment_id = ar.assessment_id
                JOIN class_subjects AS cs
                    ON cs.class_subject_id = existing.class_subject_id
                JOIN teacher_class_subjects AS tcs
                    ON tcs.class_subject_id = cs.class_subject_id
                JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
                JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
                WHERE t.user_id = %s
                  AND existing.assessment_id = %s
                  AND ar.obtained_marks > %s
            )
            """,
            (user_id, assessment_id, max_marks),
        )
        if cursor.fetchone()[0]:
            return -1
        cursor.execute(
            """
            UPDATE assessments AS a
            JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
            JOIN teacher_class_subjects AS tcs
                ON tcs.class_subject_id = cs.class_subject_id
            JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
            JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
            SET a.assessment_type = %s,
                a.title = %s,
                a.assessment_date = %s,
                a.max_marks = %s
            WHERE t.user_id = %s AND a.assessment_id = %s
            """,
            (
                assessment_type,
                title,
                assessment_date,
                max_marks,
                user_id,
                assessment_id,
            ),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def delete_assessment(connection, user_id, assessment_id):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT a.assessment_id
            FROM assessments AS a
            JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
            JOIN teacher_class_subjects AS tcs
                ON tcs.class_subject_id = cs.class_subject_id
            JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
            JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
            WHERE t.user_id = %s AND a.assessment_id = %s
            LIMIT 1
            """,
            (user_id, assessment_id),
        )
        if cursor.fetchone() is None:
            return 0
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM assessment_results WHERE assessment_id = %s)",
            (assessment_id,),
        )
        if cursor.fetchone()[0]:
            return -1
        cursor.execute(
            """
            DELETE a
            FROM assessments AS a
            JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
            JOIN teacher_class_subjects AS tcs
                ON tcs.class_subject_id = cs.class_subject_id
            JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
            JOIN users AS u ON u.user_id = t.user_id AND u.is_active = TRUE
            WHERE t.user_id = %s AND a.assessment_id = %s
            """,
            (user_id, assessment_id),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def upsert_assessment_result(
    connection, user_id, assessment_id, student_id, obtained_marks
):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT a.assessment_id
            FROM assessments AS a
            JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
            JOIN teacher_class_subjects AS tcs
                ON tcs.class_subject_id = cs.class_subject_id
            JOIN teachers AS t ON t.teacher_id = tcs.teacher_id
            JOIN users AS teacher_user ON teacher_user.user_id = t.user_id
                AND teacher_user.is_active = TRUE
            JOIN class_students AS enrolled ON enrolled.class_id = cs.class_id
                AND enrolled.student_id = %s
            WHERE t.user_id = %s AND a.assessment_id = %s
            FOR UPDATE
            """,
            (student_id, user_id, assessment_id),
        )
        if cursor.fetchone() is None:
            return 0
        cursor.execute(
            """
            INSERT INTO assessment_results (assessment_id, student_id, obtained_marks)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE obtained_marks = VALUES(obtained_marks)
            """,
            (assessment_id, student_id, obtained_marks),
        )
        return 1
    finally:
        cursor.close()