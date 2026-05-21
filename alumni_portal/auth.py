from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from . import db
from .security import normalize_email

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        user = db.get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html")
        session.clear()
        session["user_id"] = user["id"]
        db.log_event("login", user["id"], user["id"], "User signed in.")
        db.get_db().commit()
        flash("Signed in successfully.", "success")
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("portal.profile"))
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        db.log_event("logout", user_id, user_id, "User signed out.")
        db.get_db().commit()
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("portal.home"))
