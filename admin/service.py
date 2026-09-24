from werkzeug.security import generate_password_hash

from admin import repository


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


class ConflictError(ValueError):
    pass


def _text(value, label, maximum):
    value = value.strip()
    if not value:
        raise ValidationError(f"{label} is required.")
    if len(value) > maximum:
        raise ValidationError(f"{label} must be {maximum} characters or fewer.")
    return value


def _id(value, label):
    try:
        value = int(value)
    except (TypeError, ValueError) as error:
        raise ValidationError(f"Select a valid {label}.") from error
    if value <= 0:
        raise ValidationError(f"Select a valid {label}.")
    return value


def _account_values(form, include_password):
    full_name = _text(form.get("full_name", ""), "Full name", 150)
    identifier = _text(form.get("login_identifier", ""), "Login identifier", 100)
    password = form.get("password", "")
    if include_password:
        if len(password) < 8:
            raise ValidationError("Password must contain at least 8 characters.")
    return full_name, identifier, password


def _new_password(form):
    password = form.get("password", "")
    confirmation = form.get("password_confirmation", "")
    if len(password) < 8:
        raise ValidationError("Password must contain at least 8 characters.")
    if password != confirmation:
        raise ValidationError("New passwords do not match.")
    return password


def validate_student_form(form, include_password):
    full_name, identifier, password = _account_values(form, include_password)
    student_number = _text(form.get("student_number", ""), "Student number", 50)
    return student_number, full_name, identifier, password


def validate_teacher_form(form, include_password):
    full_name, identifier, password = _account_values(form, include_password)
    teacher_number = _text(form.get("teacher_number", ""), "Teacher number", 50)
    return teacher_number, full_name, identifier, password


def validate_admin_form(form):
    return _account_values(form, True)


def validate_class_form(form):
    return (
        _text(form.get("class_name", ""), "Class name", 100),
        _text(form.get("academic_year", ""), "Academic year", 20),
    )


def validate_subject_form(form):
    return (
        _text(form.get("subject_code", ""), "Subject code", 30),
        _text(form.get("subject_name", ""), "Subject name", 150),
    )


def validate_assignment_form(form):
    return (
        _id(form.get("teacher_id"), "teacher"),
        _id(form.get("class_subject_id"), "class subject"),
    )


def create_student(form):
    student_number, full_name, identifier, password = validate_student_form(form, True)
    with repository.transaction() as connection:
        return repository.create_student(
            connection,
            student_number,
            full_name,
            identifier,
            generate_password_hash(password),
        )


def update_student(student_id, form):
    student_id = _id(student_id, "student")
    student_number, full_name, identifier, _ = validate_student_form(form, False)
    with repository.transaction() as connection:
        if repository.update_student(
            connection, student_id, student_number, full_name, identifier
        ) == 0:
            raise NotFoundError("Student was not found.")


def deactivate_student(student_id):
    student_id = _id(student_id, "student")
    with repository.transaction() as connection:
        if repository.deactivate_student(connection, student_id) == 0:
            raise NotFoundError("Student was not found.")


def reset_student_password(student_id, form):
    student_id = _id(student_id, "student")
    password = _new_password(form)
    with repository.transaction() as connection:
        if repository.reset_student_password(
            connection, student_id, generate_password_hash(password)
        ) == 0:
            raise NotFoundError("Student was not found.")


def create_teacher(form):
    teacher_number, full_name, identifier, password = validate_teacher_form(form, True)
    with repository.transaction() as connection:
        return repository.create_teacher(
            connection,
            teacher_number,
            full_name,
            identifier,
            generate_password_hash(password),
        )


def create_admin(form):
    _, identifier, password = validate_admin_form(form)
    with repository.transaction() as connection:
        return repository.create_admin(
            connection, identifier, generate_password_hash(password)
        )


def update_teacher(teacher_id, form):
    teacher_id = _id(teacher_id, "teacher")
    teacher_number, full_name, identifier, _ = validate_teacher_form(form, False)
    with repository.transaction() as connection:
        if repository.update_teacher(
            connection, teacher_id, teacher_number, full_name, identifier
        ) == 0:
            raise NotFoundError("Teacher was not found.")


def deactivate_teacher(teacher_id):
    teacher_id = _id(teacher_id, "teacher")
    with repository.transaction() as connection:
        if repository.deactivate_teacher(connection, teacher_id) == 0:
            raise NotFoundError("Teacher was not found.")


def reset_teacher_password(teacher_id, form):
    teacher_id = _id(teacher_id, "teacher")
    password = _new_password(form)
    with repository.transaction() as connection:
        if repository.reset_teacher_password(
            connection, teacher_id, generate_password_hash(password)
        ) == 0:
            raise NotFoundError("Teacher was not found.")


def create_class(form):
    class_name, academic_year = validate_class_form(form)
    with repository.transaction() as connection:
        return repository.create_class(connection, class_name, academic_year)


def update_class(class_id, form):
    class_id = _id(class_id, "class")
    class_name, academic_year = validate_class_form(form)
    with repository.transaction() as connection:
        if repository.update_class(connection, class_id, class_name, academic_year) == 0:
            raise NotFoundError("Class was not found.")


def delete_class(class_id):
    class_id = _id(class_id, "class")
    with repository.transaction() as connection:
        if repository.delete_class(connection, class_id) == 0:
            raise NotFoundError("Class was not found.")


def enroll_student(class_id, form):
    class_id = _id(class_id, "class")
    student_id = _id(form.get("student_id"), "student")
    with repository.transaction() as connection:
        repository.enroll_student(connection, class_id, student_id)


def remove_student_from_class(class_id, student_id):
    class_id = _id(class_id, "class")
    student_id = _id(student_id, "student")
    with repository.transaction() as connection:
        result = repository.remove_student_from_class(connection, class_id, student_id)
        if result == -1:
            raise ConflictError("Student cannot be removed while class academic records exist.")
        if result == 0:
            raise NotFoundError("Enrollment was not found.")


def add_class_subject(class_id, form):
    class_id = _id(class_id, "class")
    subject_id = _id(form.get("subject_id"), "subject")
    with repository.transaction() as connection:
        return repository.add_class_subject(connection, class_id, subject_id)


def remove_class_subject(class_id, class_subject_id):
    class_id = _id(class_id, "class")
    class_subject_id = _id(class_subject_id, "class subject")
    with repository.transaction() as connection:
        result = repository.remove_class_subject(connection, class_id, class_subject_id)
        if result == -1:
            raise ConflictError("Subject cannot be removed while assignments or assessments exist.")
        if result == 0:
            raise NotFoundError("Class-subject relationship was not found.")


def create_subject(form):
    subject_code, subject_name = validate_subject_form(form)
    with repository.transaction() as connection:
        return repository.create_subject(connection, subject_code, subject_name)


def update_subject(subject_id, form):
    subject_id = _id(subject_id, "subject")
    subject_code, subject_name = validate_subject_form(form)
    with repository.transaction() as connection:
        if repository.update_subject(connection, subject_id, subject_code, subject_name) == 0:
            raise NotFoundError("Subject was not found.")


def delete_subject(subject_id):
    subject_id = _id(subject_id, "subject")
    with repository.transaction() as connection:
        if repository.delete_subject(connection, subject_id) == 0:
            raise NotFoundError("Subject was not found.")


def create_assignment(form):
    teacher_id, class_subject_id = validate_assignment_form(form)
    with repository.transaction() as connection:
        assignment_id = repository.create_assignment(connection, teacher_id, class_subject_id)
        if assignment_id == 0:
            raise NotFoundError("The selected class-subject relationship was not found.")
        return assignment_id


def delete_assignment(assignment_id):
    assignment_id = _id(assignment_id, "assignment")
    with repository.transaction() as connection:
        if repository.delete_assignment(connection, assignment_id) == 0:
            raise NotFoundError("Assignment was not found.")