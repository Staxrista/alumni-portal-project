from functools import wraps

from flask import flash, g, redirect, url_for


def normalize_email(email):
    return email.strip().lower()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.get("user") is None:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.get("user") is None:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if g.user["role"] not in roles:
                flash("You do not have permission to access that area.", "error")
                return redirect(url_for("portal.home"))
            return view(**kwargs)

        return wrapped_view

    return decorator
