import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from auth.service import authenticate_user


auth = Blueprint("auth", __name__, url_prefix="/auth")

ROLE_HOME_ENDPOINTS = {
    "admin": "admin.dashboard",
    "teacher": "teacher_home",
    "student": "student.dashboard",
}


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    login_identifier = request.form.get("login_identifier", "").strip()
    password = request.form.get("password", "")

    if not login_identifier or not password:
        flash("Enter your login identifier and password.", "error")
        return render_template("login.html"), 400

    try:
        user = authenticate_user(login_identifier, password)
    except mysql.connector.Error:
        current_app.logger.exception("Database error during login")
        flash("Login is temporarily unavailable. Please try again later.", "error")
        return render_template("login.html"), 503
    except RuntimeError:
        current_app.logger.exception("Database configuration error during login")
        flash("Login is temporarily unavailable. Please try again later.", "error")
        return render_template("login.html"), 503

    if user is None:
        flash("Invalid login identifier or password.", "error")
        return render_template("login.html"), 401

    endpoint = ROLE_HOME_ENDPOINTS.get(user["role"])
    if endpoint is None:
        current_app.logger.error("Unsupported role returned for user %s", user["user_id"])
        flash("This account cannot access the application.", "error")
        return render_template("login.html"), 403

    session.clear()
    session.permanent = True
    session["user_id"] = user["user_id"]
    session["role"] = user["role"]
    return redirect(url_for(endpoint))


@auth.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))