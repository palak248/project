import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from auth.decorators import role_required
from auth.service import valid_csrf_token
from teacher import repository
from teacher import service


teacher = Blueprint("teacher", __name__, url_prefix="/teacher")


def _user_id():
    return session["user_id"]


def _database_failure(message):
    current_app.logger.exception("Teacher database operation failed")
    flash(message, "error")
    return render_template("500.html"), 503


@teacher.get("")
@role_required("teacher")
def dashboard():
    try:
        profile = repository.get_profile(_user_id())
        summary = repository.get_dashboard_summary(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your teacher dashboard is temporarily unavailable.")
    if profile is None or summary is None:
        return render_template("404.html"), 404
    return render_template("teacher/dashboard.html", profile=profile, summary=summary)


@teacher.get("/classes")
@role_required("teacher")
def classes():
    try:
        rows = repository.list_classes(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your assigned classes are temporarily unavailable.")
    return render_template("teacher/classes.html", classes=rows)


@teacher.get("/subjects")
@role_required("teacher")
def subjects():
    try:
        rows = repository.list_assignments(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your assigned subjects are temporarily unavailable.")
    return render_template("teacher/subjects.html", assignments=rows)


@teacher.get("/classes/<int:class_id>")
@role_required("teacher")
def class_detail(class_id):
    try:
        class_record = repository.get_class_for_teacher(_user_id(), class_id)
        if class_record is None:
            return render_template("404.html"), 404
        assignments = repository.list_class_assignments(_user_id(), class_id)
        students = repository.list_class_students(_user_id(), class_id)
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("The assigned class is temporarily unavailable.")
    return render_template(
        "teacher/class_detail.html",
        class_record=class_record,
        assignments=assignments,
        students=students,
    )


@teacher.get("/subjects/<int:class_subject_id>")
@role_required("teacher")
def subject_detail(class_subject_id):
    try:
        subject = repository.get_subject_for_teacher(_user_id(), class_subject_id)
        if subject is None:
            return render_template("404.html"), 404
        students = repository.list_subject_students(_user_id(), class_subject_id)
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("The assigned subject is temporarily unavailable.")
    return render_template("teacher/subject_detail.html", subject=subject, students=students)


@teacher.get("/attendance")
@role_required("teacher")
def attendance():
    try:
        records = repository.list_attendance(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your attendance records are temporarily unavailable.")
    return render_template("teacher/attendance.html", records=records)


@teacher.route("/subjects/<int:class_subject_id>/attendance", methods=["GET", "POST"])
@role_required("teacher")
def subject_attendance(class_subject_id):
    try:
        subject = repository.get_subject_for_teacher(_user_id(), class_subject_id)
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("The assigned subject is temporarily unavailable.")
    if subject is None:
        return render_template("404.html"), 404

    if request.method == "POST":
        if not valid_csrf_token(request.form.get("csrf_token")):
            flash("Your form session expired. Please try again.", "error")
            return redirect(url_for("teacher.subject_attendance", class_subject_id=class_subject_id))
        try:
            service.save_attendance(_user_id(), class_subject_id, request.form)
            attendance_date = service.parse_attendance_date(
                request.form.get("attendance_date", "")
            )
        except service.ValidationError as error:
            flash(str(error), "error")
            return _render_attendance_form(subject, class_subject_id, request.form.get("attendance_date", ""), 400)
        except service.NotFoundError:
            return render_template("404.html"), 404
        except (mysql.connector.Error, RuntimeError):
            return _database_failure("Attendance could not be saved.")
        flash("Attendance saved successfully.", "success")
        return redirect(
            url_for(
                "teacher.subject_attendance",
                class_subject_id=class_subject_id,
                attendance_date=attendance_date.isoformat(),
            )
        )

    attendance_date = request.args.get("attendance_date", "")
    if attendance_date:
        try:
            parsed_date = service.parse_attendance_date(attendance_date)
        except service.ValidationError as error:
            flash(str(error), "error")
            return _render_attendance_form(subject, class_subject_id, attendance_date, 400)
        return _render_attendance_form(
            subject, class_subject_id, parsed_date.isoformat(), 200
        )
    return render_template(
        "teacher/subject_attendance.html",
        subject=subject,
        attendance_date="",
        students=[],
    )


def _render_attendance_form(subject, class_subject_id, attendance_date, status_code):
    students = []
    if attendance_date:
        try:
            parsed_date = service.parse_attendance_date(attendance_date)
            students = repository.list_attendance_students(
                _user_id(), class_subject_id, parsed_date
            )
        except service.ValidationError:
            pass
        except (mysql.connector.Error, RuntimeError):
            return _database_failure("Attendance students could not be loaded.")
    return (
        render_template(
            "teacher/subject_attendance.html",
            subject=subject,
            attendance_date=attendance_date,
            students=students,
        ),
        status_code,
    )


@teacher.get("/assessments")
@role_required("teacher")
def assessments():
    try:
        rows = repository.list_assessments(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your assessments are temporarily unavailable.")
    return render_template("teacher/assessments.html", assessments=rows, subject=None)


@teacher.get("/subjects/<int:class_subject_id>/assessments")
@role_required("teacher")
def subject_assessments(class_subject_id):
    try:
        subject = repository.get_subject_for_teacher(_user_id(), class_subject_id)
        if subject is None:
            return render_template("404.html"), 404
        rows = repository.list_assessments(_user_id(), class_subject_id)
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your subject assessments are temporarily unavailable.")
    return render_template("teacher/assessments.html", assessments=rows, subject=subject)


@teacher.route("/subjects/<int:class_subject_id>/assessments/new", methods=["GET", "POST"])
@role_required("teacher")
def new_assessment(class_subject_id):
    try:
        subject = repository.get_subject_for_teacher(_user_id(), class_subject_id)
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("The assigned subject is temporarily unavailable.")
    if subject is None:
        return render_template("404.html"), 404
    if request.method == "GET":
        return render_template("teacher/assessment_form.html", assessment=None, subject=subject)
    if not valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return render_template("teacher/assessment_form.html", assessment=None, subject=subject), 400
    form = request.form.to_dict()
    form["class_subject_id"] = class_subject_id
    try:
        service.create_assessment(_user_id(), form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("teacher/assessment_form.html", assessment=None, subject=subject), 400
    except service.NotFoundError:
        return render_template("404.html"), 404
    except mysql.connector.IntegrityError:
        flash("Assessment could not be created for this subject.", "error")
        return render_template("teacher/assessment_form.html", assessment=None, subject=subject), 409
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Assessment could not be created.")
    flash("Assessment created successfully.", "success")
    return redirect(url_for("teacher.subject_assessments", class_subject_id=class_subject_id))


@teacher.route("/assessments/<int:assessment_id>/edit", methods=["GET", "POST"])
@role_required("teacher")
def edit_assessment(assessment_id):
    try:
        assessment = repository.get_assessment_for_teacher(_user_id(), assessment_id)
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Assessment could not be loaded.")
    if assessment is None:
        return render_template("404.html"), 404
    if request.method == "GET":
        return render_template("teacher/assessment_form.html", assessment=assessment, subject=assessment)
    if not valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return render_template("teacher/assessment_form.html", assessment=assessment, subject=assessment), 400
    try:
        service.update_assessment(_user_id(), assessment_id, request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("teacher/assessment_form.html", assessment=assessment, subject=assessment), 400
    except service.ConflictError as error:
        flash(str(error), "error")
        return render_template("teacher/assessment_form.html", assessment=assessment, subject=assessment), 409
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Assessment could not be updated.")
    flash("Assessment updated successfully.", "success")
    return redirect(url_for("teacher.assessments"))


@teacher.post("/assessments/<int:assessment_id>/delete")
@role_required("teacher")
def delete_assessment(assessment_id):
    if not valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return redirect(url_for("teacher.assessments"))
    try:
        service.delete_assessment(_user_id(), assessment_id)
    except service.ConflictError as error:
        flash(str(error), "error")
    except service.NotFoundError:
        return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Assessment could not be deleted.")
    else:
        flash("Assessment deleted successfully.", "success")
    return redirect(url_for("teacher.assessments"))


@teacher.route("/assessments/<int:assessment_id>/marks", methods=["GET", "POST"])
@role_required("teacher")
def assessment_marks(assessment_id):
    try:
        assessment = repository.get_assessment_for_teacher(_user_id(), assessment_id)
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Assessment marks could not be loaded.")
    if assessment is None:
        return render_template("404.html"), 404
    if request.method == "POST":
        if not valid_csrf_token(request.form.get("csrf_token")):
            flash("Your form session expired. Please try again.", "error")
            return redirect(url_for("teacher.assessment_marks", assessment_id=assessment_id))
        try:
            service.save_marks(_user_id(), assessment_id, request.form)
        except service.ValidationError as error:
            flash(str(error), "error")
            students = repository.list_assessment_students(_user_id(), assessment_id)
            return render_template("teacher/marks.html", assessment=assessment, students=students), 400
        except service.NotFoundError:
            return render_template("404.html"), 404
        except (mysql.connector.Error, RuntimeError):
            return _database_failure("Marks could not be saved.")
        flash("Marks saved successfully.", "success")
        return redirect(url_for("teacher.assessment_marks", assessment_id=assessment_id))
    try:
        students = repository.list_assessment_students(_user_id(), assessment_id)
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Assessment students could not be loaded.")
    return render_template("teacher/marks.html", assessment=assessment, students=students)