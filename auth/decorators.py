from functools import wraps

import mysql.connector
from flask import current_app, flash, redirect, render_template, session, url_for

from auth.service import get_active_user_role


def _verify_session(allowed_roles=None):
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))

    try:
        role = get_active_user_role(session["user_id"])
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Could not verify authenticated session")
        session.clear()
        flash("Your session could not be verified. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    if role is None:
        session.clear()
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login"))

    session["role"] = role
    if allowed_roles is not None and role not in allowed_roles:
        return render_template("403.html"), 403
    return None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        response = _verify_session()
        if response is not None:
            return response
        return view(*args, **kwargs)

    return wrapped_view


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            response = _verify_session(allowed_roles)
            if response is not None:
                return response
            return view(*args, **kwargs)

        return wrapped_view

    return decorator