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
        SELECT s.student_id, s.student_number, s.full_name,
               u.login_identifier, u.is_active
        FROM students AS s
        JOIN users AS u ON u.user_id = s.user_id
        WHERE s.user_id = %s AND u.is_active = TRUE
        """,
        (user_id,),
    )


def get_dashboard_summary(user_id):
    return _fetch_one(
        """
        SELECT
            COUNT(DISTINCT ar.assessment_result_id) AS result_count,
            COALESCE(SUM(ar.obtained_marks), 0) AS obtained_marks,
            COALESCE(SUM(a.max_marks), 0) AS maximum_marks,
            COUNT(DISTINCT cs.subject_id) AS subject_count,
            (
                SELECT COUNT(*)
                FROM attendance AS att
                JOIN students AS st_att ON st_att.student_id = att.student_id
                WHERE st_att.user_id = %s
            ) AS attendance_count
        FROM students AS s
        LEFT JOIN assessment_results AS ar ON ar.student_id = s.student_id
        LEFT JOIN assessments AS a ON a.assessment_id = ar.assessment_id
        LEFT JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
        WHERE s.user_id = %s AND EXISTS (
            SELECT 1 FROM users AS u WHERE u.user_id = s.user_id AND u.is_active = TRUE
        )
        """,
        (user_id, user_id),
    )


def list_results(user_id, assessment_type=None):
    conditions = ["u.user_id = %s", "u.is_active = TRUE"]
    parameters = [user_id]
    if assessment_type is not None:
        conditions.append("a.assessment_type = %s")
        parameters.append(assessment_type)

    return _fetch_all(
        f"""
        SELECT a.assessment_id, a.assessment_type, a.title, a.assessment_date,
               a.max_marks, ar.obtained_marks,
               s.subject_code, s.subject_name,
               c.class_name, c.academic_year
        FROM assessment_results AS ar
        JOIN assessments AS a ON a.assessment_id = ar.assessment_id
        JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        JOIN classes AS c ON c.class_id = cs.class_id
        JOIN students AS st ON st.student_id = ar.student_id
        JOIN users AS u ON u.user_id = st.user_id
        WHERE {' AND '.join(conditions)}
        ORDER BY a.assessment_date DESC, s.subject_name, a.title
        """,
        parameters,
    )


def list_subject_performance(user_id):
    return _fetch_all(
        """
        SELECT s.subject_code, s.subject_name,
               COUNT(DISTINCT ar.assessment_result_id) AS result_count,
               COALESCE(SUM(ar.obtained_marks), 0) AS obtained_marks,
               COALESCE(SUM(a.max_marks), 0) AS maximum_marks
        FROM assessment_results AS ar
        JOIN assessments AS a ON a.assessment_id = ar.assessment_id
        JOIN class_subjects AS cs ON cs.class_subject_id = a.class_subject_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        JOIN students AS st ON st.student_id = ar.student_id
        JOIN users AS u ON u.user_id = st.user_id
        WHERE u.user_id = %s AND u.is_active = TRUE
        GROUP BY s.subject_id, s.subject_code, s.subject_name
        ORDER BY s.subject_name, s.subject_code
        """,
        (user_id,),
    )


def list_attendance(user_id):
    return _fetch_all(
        """
        SELECT att.attendance_date, att.status,
               s.subject_code, s.subject_name,
               c.class_name, c.academic_year
        FROM attendance AS att
        JOIN class_subjects AS cs ON cs.class_subject_id = att.class_subject_id
        JOIN subjects AS s ON s.subject_id = cs.subject_id
        JOIN classes AS c ON c.class_id = cs.class_id
        JOIN students AS st ON st.student_id = att.student_id
        JOIN users AS u ON u.user_id = st.user_id
        WHERE u.user_id = %s AND u.is_active = TRUE
        ORDER BY att.attendance_date DESC, s.subject_name
        """,
        (user_id,),
    )