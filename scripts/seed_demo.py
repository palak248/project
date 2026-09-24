#!/usr/bin/env python3
"""Insert fake demonstration data into a development MySQL database.

This script is intentionally insert-only. It never drops, truncates, resets,
or deletes rows. Use a disposable local database and set MYSQL_* environment
variables before running it.
"""

import argparse
import os
from datetime import date, timedelta

import mysql.connector
from werkzeug.security import generate_password_hash


REQUIRED_TABLES = (
    "users",
    "students",
    "teachers",
    "classes",
    "subjects",
    "class_students",
    "class_subjects",
    "teacher_class_subjects",
    "assessments",
    "assessment_results",
    "attendance",
)

DEMO_PASSWORDS = {
    "admin": "DemoAdmin!2026",
    "teacher": "DemoTeacher!2026",
    "student": "DemoStudent!2026",
}


def build_plan(today=None):
    today = today or date.today()
    users = [
        ("demo_admin", "admin", "Demo Admin"),
        ("demo_teacher_1", "teacher", "Demo Teacher One"),
        ("demo_teacher_2", "teacher", "Demo Teacher Two"),
        ("demo_teacher_3", "teacher", "Demo Teacher Three"),
        ("demo_student_1", "student", "Demo Student One"),
        ("demo_student_2", "student", "Demo Student Two"),
        ("demo_student_3", "student", "Demo Student Three"),
        ("demo_student_4", "student", "Demo Student Four"),
        ("demo_student_5", "student", "Demo Student Five"),
        ("demo_student_6", "student", "Demo Student Six"),
    ]
    teachers = [
        ("demo_teacher_1", "DEMO-T-001", "Demo Teacher One"),
        ("demo_teacher_2", "DEMO-T-002", "Demo Teacher Two"),
        ("demo_teacher_3", "DEMO-T-003", "Demo Teacher Three"),
    ]
    students = [
        ("demo_student_1", "DEMO-S-001", "Demo Student One"),
        ("demo_student_2", "DEMO-S-002", "Demo Student Two"),
        ("demo_student_3", "DEMO-S-003", "Demo Student Three"),
        ("demo_student_4", "DEMO-S-004", "Demo Student Four"),
        ("demo_student_5", "DEMO-S-005", "Demo Student Five"),
        ("demo_student_6", "DEMO-S-006", "Demo Student Six"),
    ]
    classes = [
        ("DEMO-Science-A", "2026-Demo"),
        ("DEMO-Science-B", "2026-Demo"),
    ]
    subjects = [
        ("DEMO-MATH", "Demo Mathematics"),
        ("DEMO-PHY", "Demo Physics"),
        ("DEMO-CS", "Demo Computing"),
    ]
    enrollments = {
        "DEMO-Science-A": ["DEMO-S-001", "DEMO-S-002", "DEMO-S-003"],
        "DEMO-Science-B": ["DEMO-S-004", "DEMO-S-005", "DEMO-S-006"],
    }
    class_subjects = {
        "DEMO-Science-A": ["DEMO-MATH", "DEMO-PHY", "DEMO-CS"],
        "DEMO-Science-B": ["DEMO-MATH", "DEMO-CS"],
    }
    assignments = [
        ("DEMO-T-001", "DEMO-Science-A", "DEMO-MATH"),
        ("DEMO-T-001", "DEMO-Science-A", "DEMO-PHY"),
        ("DEMO-T-002", "DEMO-Science-A", "DEMO-CS"),
        ("DEMO-T-002", "DEMO-Science-B", "DEMO-MATH"),
        ("DEMO-T-003", "DEMO-Science-B", "DEMO-CS"),
    ]
    assessment_specs = [
        ("DEMO-Science-A", "DEMO-MATH", "assignment", "Demo Mathematics Assignment", 20, 14),
        ("DEMO-Science-A", "DEMO-MATH", "examination", "Demo Mathematics Examination", 100, 21),
        ("DEMO-Science-A", "DEMO-PHY", "assignment", "Demo Physics Assignment", 25, 28),
        ("DEMO-Science-A", "DEMO-PHY", "examination", "Demo Physics Examination", 100, 35),
        ("DEMO-Science-A", "DEMO-CS", "assignment", "Demo Computing Assignment", 20, 42),
        ("DEMO-Science-B", "DEMO-MATH", "assignment", "Demo Mathematics B Assignment", 20, 49),
        ("DEMO-Science-B", "DEMO-CS", "examination", "Demo Computing B Examination", 100, 56),
    ]
    return {
        "users": users,
        "teachers": teachers,
        "students": students,
        "classes": classes,
        "subjects": subjects,
        "enrollments": enrollments,
        "class_subjects": class_subjects,
        "assignments": assignments,
        "assessment_specs": assessment_specs,
        "attendance_dates": [today - timedelta(days=2), today - timedelta(days=1), today],
    }


def password_for(role):
    return os.getenv(f"DEMO_{role.upper()}_PASSWORD", DEMO_PASSWORDS[role])


def connect():
    required = ("MYSQL_USER", "MYSQL_DATABASE")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing database configuration: " + ", ".join(missing)
        )
    try:
        port = int(os.getenv("MYSQL_PORT", "3306"))
    except ValueError as error:
        raise RuntimeError("MYSQL_PORT must be an integer") from error
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=port,
        user=os.environ["MYSQL_USER"],
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.environ["MYSQL_DATABASE"],
    )


def ensure_tables(cursor):
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name IN (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        REQUIRED_TABLES,
    )
    found = {row[0] for row in cursor.fetchall()}
    missing = sorted(set(REQUIRED_TABLES) - found)
    if missing:
        raise RuntimeError(
            "Required tables are missing. Apply database/schema.sql first: "
            + ", ".join(missing)
        )


def existing_row_count(cursor):
    counts = {}
    for table in REQUIRED_TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        counts[table] = cursor.fetchone()[0]
    return counts


def ensure_demo_keys_available(cursor, plan):
    login_ids = [row[0] for row in plan["users"]]
    student_numbers = [row[1] for row in plan["students"]]
    teacher_numbers = [row[1] for row in plan["teachers"]]
    subject_codes = [row[0] for row in plan["subjects"]]
    class_keys = plan["classes"]

    cursor.execute(
        "SELECT login_identifier FROM users WHERE login_identifier IN (" + ",".join(["%s"] * len(login_ids)) + ")",
        login_ids,
    )
    collisions = [row[0] for row in cursor.fetchall()]
    cursor.execute(
        "SELECT student_number FROM students WHERE student_number IN (" + ",".join(["%s"] * len(student_numbers)) + ")",
        student_numbers,
    )
    collisions.extend(row[0] for row in cursor.fetchall())
    cursor.execute(
        "SELECT teacher_number FROM teachers WHERE teacher_number IN (" + ",".join(["%s"] * len(teacher_numbers)) + ")",
        teacher_numbers,
    )
    collisions.extend(row[0] for row in cursor.fetchall())
    cursor.execute(
        "SELECT subject_code FROM subjects WHERE subject_code IN (" + ",".join(["%s"] * len(subject_codes)) + ")",
        subject_codes,
    )
    collisions.extend(row[0] for row in cursor.fetchall())
    for class_name, academic_year in class_keys:
        cursor.execute(
            "SELECT class_id FROM classes WHERE class_name = %s AND academic_year = %s",
            (class_name, academic_year),
        )
        if cursor.fetchone() is not None:
            collisions.append(f"{class_name}/{academic_year}")
    if collisions:
        raise RuntimeError(
            "Demo identifiers already exist; aborting without changing data: "
            + ", ".join(collisions)
        )


def insert_plan(connection, plan):
    cursor = connection.cursor()
    user_ids = {}
    teacher_ids = {}
    student_ids = {}
    class_ids = {}
    subject_ids = {}
    class_subject_ids = {}
    try:
        for login_identifier, role, _ in plan["users"]:
            cursor.execute(
                """
                INSERT INTO users (login_identifier, password_hash, role)
                VALUES (%s, %s, %s)
                """,
                (login_identifier, generate_password_hash(password_for(role)), role),
            )
            user_ids[login_identifier] = cursor.lastrowid

        for login_identifier, teacher_number, full_name in plan["teachers"]:
            cursor.execute(
                """
                INSERT INTO teachers (user_id, teacher_number, full_name)
                VALUES (%s, %s, %s)
                """,
                (user_ids[login_identifier], teacher_number, full_name),
            )
            teacher_ids[login_identifier] = cursor.lastrowid

        for login_identifier, student_number, full_name in plan["students"]:
            cursor.execute(
                """
                INSERT INTO students (user_id, student_number, full_name)
                VALUES (%s, %s, %s)
                """,
                (user_ids[login_identifier], student_number, full_name),
            )
            student_ids[student_number] = cursor.lastrowid

        for class_name, academic_year in plan["classes"]:
            cursor.execute(
                "INSERT INTO classes (class_name, academic_year) VALUES (%s, %s)",
                (class_name, academic_year),
            )
            class_ids[class_name] = cursor.lastrowid

        for subject_code, subject_name in plan["subjects"]:
            cursor.execute(
                "INSERT INTO subjects (subject_code, subject_name) VALUES (%s, %s)",
                (subject_code, subject_name),
            )
            subject_ids[subject_code] = cursor.lastrowid

        for class_name, student_numbers in plan["enrollments"].items():
            for student_number in student_numbers:
                cursor.execute(
                    "INSERT INTO class_students (class_id, student_id) VALUES (%s, %s)",
                    (class_ids[class_name], student_ids[student_number]),
                )

        for class_name, subject_codes in plan["class_subjects"].items():
            for subject_code in subject_codes:
                cursor.execute(
                    """
                    INSERT INTO class_subjects (class_id, subject_id)
                    VALUES (%s, %s)
                    """,
                    (class_ids[class_name], subject_ids[subject_code]),
                )
                class_subject_ids[(class_name, subject_code)] = cursor.lastrowid

        for login_identifier, class_name, subject_code in plan["assignments"]:
            cursor.execute(
                """
                INSERT INTO teacher_class_subjects (teacher_id, class_subject_id)
                VALUES (%s, %s)
                """,
                (
                    teacher_ids[login_identifier],
                    class_subject_ids[(class_name, subject_code)],
                ),
            )

        assessment_ids = []
        for class_name, subject_code, assessment_type, title, max_marks, day_offset in plan["assessment_specs"]:
            cursor.execute(
                """
                INSERT INTO assessments
                    (class_subject_id, assessment_type, title, assessment_date, max_marks)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    class_subject_ids[(class_name, subject_code)],
                    assessment_type,
                    title,
                    date.today() - timedelta(days=day_offset),
                    max_marks,
                ),
            )
            assessment_ids.append(
                (cursor.lastrowid, class_name, subject_code, max_marks)
            )

        for assessment_id, class_name, _, max_marks in assessment_ids:
            for index, student_number in enumerate(plan["enrollments"][class_name]):
                obtained_marks = min(max_marks, Decimal(str(max_marks)) * Decimal("0.55") + index * Decimal("2.50"))
                cursor.execute(
                    """
                    INSERT INTO assessment_results
                        (assessment_id, student_id, obtained_marks)
                    VALUES (%s, %s, %s)
                    """,
                    (assessment_id, student_ids[student_number], obtained_marks),
                )

        for class_name, subject_codes in plan["class_subjects"].items():
            for subject_code in subject_codes:
                class_subject_id = class_subject_ids[(class_name, subject_code)]
                for day_index, attendance_date in enumerate(plan["attendance_dates"]):
                    for student_index, student_number in enumerate(plan["enrollments"][class_name]):
                        status = "Present" if (day_index + student_index) % 3 else "Absent"
                        cursor.execute(
                            """
                            INSERT INTO attendance
                                (class_subject_id, student_id, attendance_date, status)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                class_subject_id,
                                student_ids[student_number],
                                attendance_date,
                                status,
                            ),
                        )
    finally:
        cursor.close()


def print_plan(plan):
    print("Demo seed dry run: no database connection or writes performed.")
    print(f"Users: {len(plan['users'])}")
    print(f"Classes: {len(plan['classes'])}; subjects: {len(plan['subjects'])}")
    print(f"Assessments: {len(plan['assessment_specs'])}")
    print("Attendance dates: 3 per class-subject/student combination")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Insert fake demo data into a local development database."
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Allow inserting into a non-empty database; never deletes or resets rows.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and display the seed plan without connecting or writing.",
    )
    parser.add_argument(
        "--print-credentials",
        action="store_true",
        help="Print local demo passwords after a successful seed.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    plan = build_plan()
    if args.dry_run:
        print_plan(plan)
        return 0

    connection = connect()
    try:
        cursor = connection.cursor()
        try:
            ensure_tables(cursor)
            counts = existing_row_count(cursor)
            existing_rows = sum(counts.values())
            if existing_rows and not args.allow_existing:
                raise RuntimeError(
                    "Database is not empty; aborting. Use a disposable empty database "
                    "or pass --allow-existing explicitly. No data was changed."
                )
            ensure_demo_keys_available(cursor, plan)
        finally:
            cursor.close()

        insert_plan(connection, plan)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print("Demo data inserted successfully. No existing rows were deleted or reset.")
    print("See DEMO_DATA.md for local credentials and verification steps.")
    if args.print_credentials:
        print(f"Admin: demo_admin / {password_for('admin')}")
        print(f"Teacher: demo_teacher_1 / {password_for('teacher')}")
        print(f"Student: demo_student_1 / {password_for('student')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
