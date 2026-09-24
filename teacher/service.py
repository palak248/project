from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal, InvalidOperation

from database.connection import get_db_connection
from teacher import repository


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


class ConflictError(ValueError):
    pass


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


def _id(value, label):
    try:
        value = int(value)
    except (TypeError, ValueError) as error:
        raise ValidationError(f"Select a valid {label}.") from error
    if value <= 0:
        raise ValidationError(f"Select a valid {label}.")
    return value


def _text(value, label, maximum):
    value = value.strip()
    if not value:
        raise ValidationError(f"{label} is required.")
    if len(value) > maximum:
        raise ValidationError(f"{label} must be {maximum} characters or fewer.")
    return value


def parse_attendance_date(value):
    value = value.strip()
    if not value:
        raise ValidationError("Attendance date is required.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Attendance date must be a valid date.") from None


def _attendance_status(value):
    value = value.strip()
    if not value:
        raise ValidationError("Attendance status is required.")
    if len(value) > 20:
        raise ValidationError("Attendance status must be 20 characters or fewer.")
    return value


def _decimal(value, label, minimum=None, maximum=None):
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{label} must be a valid number.") from None
    if not number.is_finite() or number.as_tuple().exponent < -2:
        raise ValidationError(f"{label} must have no more than 2 decimal places.")
    if minimum is not None and number < minimum:
        raise ValidationError(f"{label} must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ValidationError(f"{label} must be at most {maximum}.")
    return number


def _assessment_values(form, include_class_subject):
    class_subject_id = None
    if include_class_subject:
        class_subject_id = _id(form.get("class_subject_id"), "class subject")
    assessment_type = form.get("assessment_type", "")
    if assessment_type not in {"assignment", "examination"}:
        raise ValidationError("Select a valid assessment type.")
    title = _text(form.get("title", ""), "Title", 150)
    date_value = form.get("assessment_date", "").strip()
    if date_value:
        try:
            assessment_date = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Assessment date must be a valid date.") from None
    else:
        assessment_date = None
    max_marks = _decimal(
        form.get("max_marks", ""),
        "Maximum marks",
        minimum=Decimal("0.01"),
        maximum=Decimal("999999.99"),
    )
    return class_subject_id, assessment_type, title, assessment_date, max_marks


def create_assessment(user_id, form):
    class_subject_id, assessment_type, title, assessment_date, max_marks = _assessment_values(form, True)
    with transaction() as connection:
        assessment_id = repository.create_assessment(
            connection,
            user_id,
            class_subject_id,
            assessment_type,
            title,
            assessment_date,
            max_marks,
        )
        if assessment_id == 0:
            raise NotFoundError("You are not assigned to that class and subject.")
        return assessment_id


def update_assessment(user_id, assessment_id, form):
    assessment_id = _id(assessment_id, "assessment")
    _, assessment_type, title, assessment_date, max_marks = _assessment_values(form, False)
    if repository.get_assessment_for_teacher(user_id, assessment_id) is None:
        raise NotFoundError("Assessment was not found.")
    with transaction() as connection:
        result = repository.update_assessment(
            connection,
            user_id,
            assessment_id,
            assessment_type,
            title,
            assessment_date,
            max_marks,
        )
        if result == -1:
            raise ConflictError("Maximum marks cannot be lower than an existing result.")


def delete_assessment(user_id, assessment_id):
    assessment_id = _id(assessment_id, "assessment")
    with transaction() as connection:
        result = repository.delete_assessment(connection, user_id, assessment_id)
        if result == -1:
            raise ConflictError("Assessment cannot be deleted while marks exist.")
        if result == 0:
            raise NotFoundError("Assessment was not found.")


def save_marks(user_id, assessment_id, form):
    assessment_id = _id(assessment_id, "assessment")
    assessment = repository.get_assessment_for_teacher(user_id, assessment_id)
    if assessment is None:
        raise NotFoundError("Assessment was not found.")
    students = repository.list_assessment_students(user_id, assessment_id)
    student_ids = {student["student_id"] for student in students}
    entries = []
    for field_name, raw_value in form.items():
        if not field_name.startswith("marks_"):
            continue
        student_id = _id(field_name[6:], "student")
        if student_id not in student_ids:
            raise ValidationError("That student is not enrolled in this assessment's class.")
        raw_value = raw_value.strip()
        if not raw_value:
            continue
        obtained_marks = _decimal(
            raw_value,
            "Obtained marks",
            minimum=Decimal("0"),
            maximum=Decimal(str(assessment["max_marks"])),
        )
        entries.append((student_id, obtained_marks))
    if not entries:
        raise ValidationError("Enter at least one mark.")
    with transaction() as connection:
        for student_id, obtained_marks in entries:
            if repository.upsert_assessment_result(
                connection, user_id, assessment_id, student_id, obtained_marks
            ) == 0:
                raise NotFoundError("Assessment or enrolled student was not found.")


def save_attendance(user_id, class_subject_id, form):
    class_subject_id = _id(class_subject_id, "class subject")
    attendance_date = parse_attendance_date(form.get("attendance_date", ""))
    if repository.get_subject_for_teacher(user_id, class_subject_id) is None:
        raise NotFoundError("The assigned subject was not found.")
    students = repository.list_attendance_students(
        user_id, class_subject_id, attendance_date
    )
    student_ids = {student["student_id"] for student in students}
    entries = []
    for field_name, raw_value in form.items():
        if not field_name.startswith("status_"):
            continue
        student_id = _id(field_name[7:], "student")
        if student_id not in student_ids:
            raise ValidationError("That student is not enrolled in this subject's class.")
        raw_value = raw_value.strip()
        if not raw_value:
            continue
        entries.append((student_id, _attendance_status(raw_value)))
    if not entries:
        raise ValidationError("Enter at least one attendance status.")
    with transaction() as connection:
        for student_id, status in entries:
            if repository.upsert_attendance(
                connection,
                user_id,
                class_subject_id,
                student_id,
                attendance_date,
                status,
            ) == 0:
                raise NotFoundError("Subject or enrolled student was not found.")