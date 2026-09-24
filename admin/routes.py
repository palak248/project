import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from admin import repository, service
from auth.decorators import role_required
from auth.service import valid_csrf_token


admin = Blueprint("admin", __name__, url_prefix="/admin")


def _database_error(message):
    current_app.logger.exception("Administrative database operation failed")
    flash(message, "error")


def _csrf_error():
    flash("Your form session expired. Please try again.", "error")


@admin.get("")
@role_required("admin")
def dashboard():
    try:
        counts = repository.dashboard_counts()
    except (mysql.connector.Error, RuntimeError):
        _database_error("The dashboard is temporarily unavailable.")
        counts = {
            "student_count": 0,
            "teacher_count": 0,
            "class_count": 0,
            "subject_count": 0,
            "assignment_count": 0,
        }
    return render_template("admin/dashboard.html", counts=counts)


@admin.get("/admins")
@role_required("admin")
def admins():
    try:
        rows = repository.list_admins()
    except (mysql.connector.Error, RuntimeError):
        _database_error("Administrators could not be loaded.")
        rows = []
    return render_template("admin/admins.html", admins=rows)


@admin.route("/admins/new", methods=["GET", "POST"])
@role_required("admin")
def new_admin():
    if request.method == "GET":
        return render_template("admin/admin_form.html")
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/admin_form.html"), 400
    try:
        service.create_admin(request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/admin_form.html"), 400
    except mysql.connector.IntegrityError:
        flash("That login identifier already exists.", "error")
        return render_template("admin/admin_form.html"), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Administrator could not be created.")
        return render_template("admin/admin_form.html"), 503
    flash("Administrator created successfully.", "success")
    return redirect(url_for("admin.admins"))


@admin.get("/students")
@role_required("admin")
def students():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "all")
    if status not in {"all", "active", "inactive"}:
        status = "all"
    try:
        rows = repository.list_students(search, status)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Students could not be loaded.")
        rows = []
    return render_template("admin/students.html", students=rows, search=search, status=status)


@admin.route("/students/new", methods=["GET", "POST"])
@role_required("admin")
def new_student():
    if request.method == "GET":
        return render_template("admin/student_form.html", student=None)
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/student_form.html", student=None), 400
    try:
        service.create_student(request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/student_form.html", student=None), 400
    except mysql.connector.IntegrityError:
        flash("Student number or login identifier already exists.", "error")
        return render_template("admin/student_form.html", student=None), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student could not be created.")
        return render_template("admin/student_form.html", student=None), 503
    flash("Student created successfully.", "success")
    return redirect(url_for("admin.students"))


@admin.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_student(student_id):
    try:
        student = repository.get_student(student_id)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student could not be loaded.")
        return redirect(url_for("admin.students"))
    if student is None:
        return render_template("404.html"), 404
    if request.method == "GET":
        return render_template("admin/student_form.html", student=student)
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/student_form.html", student=student), 400
    try:
        service.update_student(student_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/student_form.html", student=student), 400
    except service.NotFoundError:
        return render_template("404.html"), 404
    except mysql.connector.IntegrityError:
        flash("Student number or login identifier already exists.", "error")
        return render_template("admin/student_form.html", student=student), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student could not be updated.")
        return render_template("admin/student_form.html", student=student), 503
    flash("Student updated successfully.", "success")
    return redirect(url_for("admin.students"))


@admin.post("/students/<int:student_id>/deactivate")
@role_required("admin")
def deactivate_student(student_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.students"))
    try:
        service.deactivate_student(student_id)
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student could not be deactivated.")
        return redirect(url_for("admin.students"))
    flash("Student account deactivated.", "success")
    return redirect(url_for("admin.students"))


@admin.route("/students/<int:student_id>/password", methods=["GET", "POST"])
@role_required("admin")
def reset_student_password(student_id):
    try:
        student = repository.get_student(student_id)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student account could not be loaded.")
        return redirect(url_for("admin.students"))
    if student is None:
        return render_template("404.html"), 404
    if request.method == "GET":
        return render_template("admin/password_reset_form.html", account=student, account_type="student")
    if not valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return render_template("admin/password_reset_form.html", account=student, account_type="student"), 400
    try:
        service.reset_student_password(student_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/password_reset_form.html", account=student, account_type="student"), 400
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student password could not be reset.")
        return render_template("admin/password_reset_form.html", account=student, account_type="student"), 503
    flash("Student password reset successfully.", "success")
    return redirect(url_for("admin.students"))


@admin.get("/teachers")
@role_required("admin")
def teachers():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "all")
    if status not in {"all", "active", "inactive"}:
        status = "all"
    try:
        rows = repository.list_teachers(search, status)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teachers could not be loaded.")
        rows = []
    return render_template("admin/teachers.html", teachers=rows, search=search, status=status)


@admin.route("/teachers/new", methods=["GET", "POST"])
@role_required("admin")
def new_teacher():
    if request.method == "GET":
        return render_template("admin/teacher_form.html", teacher=None)
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/teacher_form.html", teacher=None), 400
    try:
        service.create_teacher(request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/teacher_form.html", teacher=None), 400
    except mysql.connector.IntegrityError:
        flash("Teacher number or login identifier already exists.", "error")
        return render_template("admin/teacher_form.html", teacher=None), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher could not be created.")
        return render_template("admin/teacher_form.html", teacher=None), 503
    flash("Teacher created successfully.", "success")
    return redirect(url_for("admin.teachers"))


@admin.route("/teachers/<int:teacher_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_teacher(teacher_id):
    try:
        teacher = repository.get_teacher(teacher_id)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher could not be loaded.")
        return redirect(url_for("admin.teachers"))
    if teacher is None:
        return render_template("404.html"), 404
    if request.method == "GET":
        return render_template("admin/teacher_form.html", teacher=teacher)
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/teacher_form.html", teacher=teacher), 400
    try:
        service.update_teacher(teacher_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/teacher_form.html", teacher=teacher), 400
    except service.NotFoundError:
        return render_template("404.html"), 404
    except mysql.connector.IntegrityError:
        flash("Teacher number or login identifier already exists.", "error")
        return render_template("admin/teacher_form.html", teacher=teacher), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher could not be updated.")
        return render_template("admin/teacher_form.html", teacher=teacher), 503
    flash("Teacher updated successfully.", "success")
    return redirect(url_for("admin.teachers"))


@admin.post("/teachers/<int:teacher_id>/deactivate")
@role_required("admin")
def deactivate_teacher(teacher_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.teachers"))
    try:
        service.deactivate_teacher(teacher_id)
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher could not be deactivated.")
        return redirect(url_for("admin.teachers"))
    flash("Teacher account deactivated.", "success")
    return redirect(url_for("admin.teachers"))


@admin.route("/teachers/<int:teacher_id>/password", methods=["GET", "POST"])
@role_required("admin")
def reset_teacher_password(teacher_id):
    try:
        teacher = repository.get_teacher(teacher_id)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher account could not be loaded.")
        return redirect(url_for("admin.teachers"))
    if teacher is None:
        return render_template("404.html"), 404
    if request.method == "GET":
        return render_template("admin/password_reset_form.html", account=teacher, account_type="teacher")
    if not valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return render_template("admin/password_reset_form.html", account=teacher, account_type="teacher"), 400
    try:
        service.reset_teacher_password(teacher_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/password_reset_form.html", account=teacher, account_type="teacher"), 400
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher password could not be reset.")
        return render_template("admin/password_reset_form.html", account=teacher, account_type="teacher"), 503
    flash("Teacher password reset successfully.", "success")
    return redirect(url_for("admin.teachers"))


@admin.get("/classes")
@role_required("admin")
def classes():
    search = request.args.get("search", "").strip()
    try:
        rows = repository.list_classes(search)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Classes could not be loaded.")
        rows = []
    return render_template("admin/classes.html", classes=rows, search=search)


@admin.get("/classes/<int:class_id>")
@role_required("admin")
def class_detail(class_id):
    try:
        class_record = repository.get_class(class_id)
        if class_record is None:
            return render_template("404.html"), 404
        students = repository.list_class_students(class_id)
        student_options = repository.list_available_students(class_id)
        class_subjects = repository.list_class_subjects(class_id)
        subject_options = repository.list_available_subjects(class_id)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Class structure could not be loaded.")
        return redirect(url_for("admin.classes"))
    return render_template(
        "admin/class_detail.html",
        class_record=class_record,
        students=students,
        student_options=student_options,
        class_subjects=class_subjects,
        subject_options=subject_options,
    )


@admin.post("/classes/<int:class_id>/students")
@role_required("admin")
def enroll_student(class_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.class_detail", class_id=class_id))
    try:
        service.enroll_student(class_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
    except mysql.connector.IntegrityError:
        flash("That student is already enrolled or the selected record is invalid.", "error")
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student could not be enrolled.")
    else:
        flash("Student enrolled successfully.", "success")
    return redirect(url_for("admin.class_detail", class_id=class_id))


@admin.post("/classes/<int:class_id>/students/<int:student_id>/remove")
@role_required("admin")
def remove_student_from_class(class_id, student_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.class_detail", class_id=class_id))
    try:
        service.remove_student_from_class(class_id, student_id)
    except service.ConflictError as error:
        flash(str(error), "error")
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student could not be removed from the class.")
    else:
        flash("Student removed from the class.", "success")
    return redirect(url_for("admin.class_detail", class_id=class_id))


@admin.post("/classes/<int:class_id>/subjects")
@role_required("admin")
def add_class_subject(class_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.class_detail", class_id=class_id))
    try:
        service.add_class_subject(class_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
    except mysql.connector.IntegrityError:
        flash("That subject is already part of this class or the selected record is invalid.", "error")
    except (mysql.connector.Error, RuntimeError):
        _database_error("Subject could not be added to the class.")
    else:
        flash("Subject added to the class.", "success")
    return redirect(url_for("admin.class_detail", class_id=class_id))


@admin.post("/classes/<int:class_id>/subjects/<int:class_subject_id>/remove")
@role_required("admin")
def remove_class_subject(class_id, class_subject_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.class_detail", class_id=class_id))
    try:
        service.remove_class_subject(class_id, class_subject_id)
    except service.ConflictError as error:
        flash(str(error), "error")
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Subject could not be removed from the class.")
    else:
        flash("Subject removed from the class.", "success")
    return redirect(url_for("admin.class_detail", class_id=class_id))


@admin.route("/classes/new", methods=["GET", "POST"])
@role_required("admin")
def new_class():
    if request.method == "GET":
        return render_template("admin/class_form.html", class_record=None)
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/class_form.html", class_record=None), 400
    try:
        service.create_class(request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/class_form.html", class_record=None), 400
    except mysql.connector.IntegrityError:
        flash("That class already exists for the academic year.", "error")
        return render_template("admin/class_form.html", class_record=None), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Class could not be created.")
        return render_template("admin/class_form.html", class_record=None), 503
    flash("Class created successfully.", "success")
    return redirect(url_for("admin.classes"))


@admin.route("/classes/<int:class_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_class(class_id):
    try:
        class_record = repository.get_class(class_id)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Class could not be loaded.")
        return redirect(url_for("admin.classes"))
    if class_record is None:
        return render_template("404.html"), 404
    if request.method == "GET":
        return render_template("admin/class_form.html", class_record=class_record)
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/class_form.html", class_record=class_record), 400
    try:
        service.update_class(class_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/class_form.html", class_record=class_record), 400
    except service.NotFoundError:
        return render_template("404.html"), 404
    except mysql.connector.IntegrityError:
        flash("That class already exists for the academic year.", "error")
        return render_template("admin/class_form.html", class_record=class_record), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Class could not be updated.")
        return render_template("admin/class_form.html", class_record=class_record), 503
    flash("Class updated successfully.", "success")
    return redirect(url_for("admin.classes"))


@admin.post("/classes/<int:class_id>/delete")
@role_required("admin")
def delete_class(class_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.classes"))
    try:
        service.delete_class(class_id)
    except service.NotFoundError:
        return render_template("404.html"), 404
    except mysql.connector.IntegrityError:
        flash("Class cannot be deleted because related records exist.", "error")
        return redirect(url_for("admin.classes"))
    except (mysql.connector.Error, RuntimeError):
        _database_error("Class could not be deleted.")
        return redirect(url_for("admin.classes"))
    flash("Class deleted successfully.", "success")
    return redirect(url_for("admin.classes"))


@admin.get("/subjects")
@role_required("admin")
def subjects():
    search = request.args.get("search", "").strip()
    try:
        rows = repository.list_subjects(search)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Subjects could not be loaded.")
        rows = []
    return render_template("admin/subjects.html", subjects=rows, search=search)


@admin.route("/subjects/new", methods=["GET", "POST"])
@role_required("admin")
def new_subject():
    if request.method == "GET":
        return render_template("admin/subject_form.html", subject=None)
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/subject_form.html", subject=None), 400
    try:
        service.create_subject(request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/subject_form.html", subject=None), 400
    except mysql.connector.IntegrityError:
        flash("That subject code already exists.", "error")
        return render_template("admin/subject_form.html", subject=None), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Subject could not be created.")
        return render_template("admin/subject_form.html", subject=None), 503
    flash("Subject created successfully.", "success")
    return redirect(url_for("admin.subjects"))


@admin.route("/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_subject(subject_id):
    try:
        subject = repository.get_subject(subject_id)
    except (mysql.connector.Error, RuntimeError):
        _database_error("Subject could not be loaded.")
        return redirect(url_for("admin.subjects"))
    if subject is None:
        return render_template("404.html"), 404
    if request.method == "GET":
        return render_template("admin/subject_form.html", subject=subject)
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return render_template("admin/subject_form.html", subject=subject), 400
    try:
        service.update_subject(subject_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("admin/subject_form.html", subject=subject), 400
    except service.NotFoundError:
        return render_template("404.html"), 404
    except mysql.connector.IntegrityError:
        flash("That subject code already exists.", "error")
        return render_template("admin/subject_form.html", subject=subject), 409
    except (mysql.connector.Error, RuntimeError):
        _database_error("Subject could not be updated.")
        return render_template("admin/subject_form.html", subject=subject), 503
    flash("Subject updated successfully.", "success")
    return redirect(url_for("admin.subjects"))


@admin.post("/subjects/<int:subject_id>/delete")
@role_required("admin")
def delete_subject(subject_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.subjects"))
    try:
        service.delete_subject(subject_id)
    except service.NotFoundError:
        return render_template("404.html"), 404
    except mysql.connector.IntegrityError:
        flash("Subject cannot be deleted because related records exist.", "error")
        return redirect(url_for("admin.subjects"))
    except (mysql.connector.Error, RuntimeError):
        _database_error("Subject could not be deleted.")
        return redirect(url_for("admin.subjects"))
    flash("Subject deleted successfully.", "success")
    return redirect(url_for("admin.subjects"))


@admin.get("/assignments")
@role_required("admin")
def assignments():
    try:
        rows = repository.list_assignments()
        options = repository.assignment_options()
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher assignments could not be loaded.")
        rows = []
        options = {"teachers": [], "class_subjects": []}
    return render_template("admin/assignments.html", assignments=rows, **options)


@admin.post("/assignments")
@role_required("admin")
def create_assignment():
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.assignments"))
    try:
        service.create_assignment(request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("admin.assignments"))
    except service.NotFoundError as error:
        flash(str(error), "error")
        return redirect(url_for("admin.assignments"))
    except mysql.connector.IntegrityError:
        flash("That teacher is already assigned to this class and subject.", "error")
        return redirect(url_for("admin.assignments"))
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher assignment could not be created.")
        return redirect(url_for("admin.assignments"))
    flash("Teacher assignment created successfully.", "success")
    return redirect(url_for("admin.assignments"))


@admin.post("/assignments/<int:assignment_id>/delete")
@role_required("admin")
def delete_assignment(assignment_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        _csrf_error()
        return redirect(url_for("admin.assignments"))
    try:
        service.delete_assignment(assignment_id)
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher assignment could not be removed.")
        return redirect(url_for("admin.assignments"))
    flash("Teacher assignment removed successfully.", "success")
    return redirect(url_for("admin.assignments"))