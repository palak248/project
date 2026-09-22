import mysql.connector
from flask import Blueprint, current_app, flash, render_template, session

from auth.decorators import role_required
from student import repository


student = Blueprint("student", __name__, url_prefix="/student")


def _database_failure(message):
    current_app.logger.exception("Student database operation failed")
    flash(message, "error")
    return render_template("500.html"), 503


def _user_id():
    return session["user_id"]


@student.get("")
@role_required("student")
def dashboard():
    try:
        profile = repository.get_profile(_user_id())
        summary = repository.get_dashboard_summary(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your dashboard is temporarily unavailable.")
    if profile is None:
        return render_template("404.html"), 404
    return render_template("student/dashboard.html", profile=profile, summary=summary)


@student.get("/profile")
@role_required("student")
def profile():
    try:
        profile = repository.get_profile(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your profile is temporarily unavailable.")
    if profile is None:
        return render_template("404.html"), 404
    return render_template("student/profile.html", profile=profile)


@student.get("/marks")
@role_required("student")
def marks():
    try:
        results = repository.list_results(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your marks are temporarily unavailable.")
    return render_template("student/results.html", results=results, title="Marks and results", filter_type="all")


@student.get("/assignments")
@role_required("student")
def assignments():
    try:
        results = repository.list_results(_user_id(), "assignment")
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your assignment results are temporarily unavailable.")
    return render_template("student/results.html", results=results, title="Assignment results", filter_type="assignment")


@student.get("/examinations")
@role_required("student")
def examinations():
    try:
        results = repository.list_results(_user_id(), "examination")
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your examination results are temporarily unavailable.")
    return render_template("student/results.html", results=results, title="Examination results", filter_type="examination")


@student.get("/performance")
@role_required("student")
def performance():
    try:
        profile = repository.get_profile(_user_id())
        summary = repository.get_dashboard_summary(_user_id())
        subjects = repository.list_subject_performance(_user_id())
        results = repository.list_results(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your performance is temporarily unavailable.")
    if profile is None:
        return render_template("404.html"), 404
    return render_template(
        "student/performance.html",
        profile=profile,
        summary=summary,
        subjects=subjects,
        results=results,
    )


@student.get("/attendance")
@role_required("student")
def attendance():
    try:
        records = repository.list_attendance(_user_id())
    except (mysql.connector.Error, RuntimeError):
        return _database_failure("Your attendance is temporarily unavailable.")
    return render_template("student/attendance.html", records=records)