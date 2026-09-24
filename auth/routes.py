import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from auth import service
from auth.decorators import login_required


auth = Blueprint("auth", __name__, url_prefix="/auth")

ROLE_HOME_ENDPOINTS = {
    "admin": "admin.dashboard",
    "teacher": "teacher.dashboard",
    "student": "student.dashboard",
}


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        setup_available = False
        try:
            setup_available = service.first_admin_setup_available()
        except (mysql.connector.Error, RuntimeError):
            current_app.logger.exception("Could not check first administrator setup")
        return render_template("login.html", setup_available=setup_available)

    login_identifier = request.form.get("login_identifier", "").strip()
    password = request.form.get("password", "")

    if not service.valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return render_template("login.html", login_identifier=login_identifier), 400

    if not login_identifier or not password:
        flash("Enter your login identifier and password.", "error")
        return render_template("login.html", login_identifier=login_identifier), 400

    try:
        user = service.authenticate_user(login_identifier, password)
    except mysql.connector.Error:
        current_app.logger.exception("Database error during login")
        flash("Login is temporarily unavailable. Please try again later.", "error")
        return render_template("login.html", login_identifier=login_identifier), 503
    except RuntimeError:
        current_app.logger.exception("Database configuration error during login")
        flash("Login is temporarily unavailable. Please try again later.", "error")
        return render_template("login.html", login_identifier=login_identifier), 503

    if user is None:
        flash("Invalid login identifier or password.", "error")
        return render_template("login.html", login_identifier=login_identifier), 401

    endpoint = ROLE_HOME_ENDPOINTS.get(user["role"])
    if endpoint is None:
        current_app.logger.error("Unsupported role returned for user %s", user["user_id"])
        flash("This account cannot access the application.", "error")
        return render_template("login.html", login_identifier=login_identifier), 403

    session.clear()
    session.permanent = True
    session["user_id"] = user["user_id"]
    session["role"] = user["role"]
    return redirect(url_for(endpoint))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if not service.valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return render_template("register.html"), 400

    try:
        service.register_student(request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("register.html"), 400
    except mysql.connector.IntegrityError:
        flash("That login identifier or student number already exists.", "error")
        return render_template("register.html"), 409
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Student registration failed")
        flash("Registration is temporarily unavailable. Please try again later.", "error")
        return render_template("register.html"), 503

    flash("Student account created. You can now log in.", "success")
    return redirect(url_for("auth.login"))


@auth.route("/setup", methods=["GET", "POST"])
def setup():
    try:
        if not service.first_admin_setup_available():
            return render_template("404.html"), 404
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Could not check first administrator setup")
        flash("First administrator setup is temporarily unavailable.", "error")
        return render_template("setup.html"), 503

    if request.method == "GET":
        return render_template("setup.html")

    if not service.valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return render_template("setup.html"), 400

    try:
        service.create_first_admin(request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("setup.html"), 400
    except service.SetupUnavailable:
        return render_template("404.html"), 404
    except mysql.connector.IntegrityError:
        flash("That login identifier is already in use.", "error")
        return render_template("setup.html"), 409
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("First administrator setup failed")
        flash("First administrator setup is temporarily unavailable.", "error")
        return render_template("setup.html"), 503

    flash("First administrator created. You can now log in.", "success")
    return redirect(url_for("auth.login"))


@auth.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "GET":
        return render_template("auth/password_form.html")

    if not service.valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return render_template("auth/password_form.html"), 400

    try:
        service.change_password(session["user_id"], request.form.get("current_password", ""), request.form)
    except service.ValidationError as error:
        flash(str(error), "error")
        return render_template("auth/password_form.html"), 400
    except service.AuthenticationError as error:
        flash(str(error), "error")
        return render_template("auth/password_form.html"), 400
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Password change failed")
        flash("Your password could not be changed right now.", "error")
        return render_template("auth/password_form.html"), 503

    session.clear()
    flash("Password changed successfully. Please log in again.", "success")
    return redirect(url_for("auth.login"))


@auth.post("/logout")
def logout():
    if not service.valid_csrf_token(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return redirect(url_for("auth.login"))
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))