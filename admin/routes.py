import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from admin import repository, service
from auth.decorators import role_required


admin = Blueprint("admin", __name__, url_prefix="/admin")


def _database_error(message):
    current_app.logger.exception("Administrative database operation failed")
    flash(message, "error")


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
    try:
        service.deactivate_student(student_id)
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Student could not be deactivated.")
        return redirect(url_for("admin.students"))
    flash("Student account deactivated.", "success")
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
    try:
        service.deactivate_teacher(teacher_id)
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher could not be deactivated.")
        return redirect(url_for("admin.teachers"))
    flash("Teacher account deactivated.", "success")
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


@admin.route("/classes/new", methods=["GET", "POST"])
@role_required("admin")
def new_class():
    if request.method == "GET":
        return render_template("admin/class_form.html", class_record=None)
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
        options = {"teachers": [], "classes": [], "subjects": []}
    return render_template("admin/assignments.html", assignments=rows, **options)


@admin.post("/assignments")
@role_required("admin")
def create_assignment():
    try:
        service.create_assignment(request.form)
    except service.ValidationError as error:
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
    try:
        service.delete_assignment(assignment_id)
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        _database_error("Teacher assignment could not be removed.")
        return redirect(url_for("admin.assignments"))
    flash("Teacher assignment removed successfully.", "success")
    return redirect(url_for("admin.assignments"))