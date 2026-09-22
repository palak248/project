from functools import wraps

from flask import flash, redirect, render_template, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login"))

            if session.get("role") not in allowed_roles:
                return render_template("403.html"), 403

            return view(*args, **kwargs)

        return wrapped_view

    return decorator