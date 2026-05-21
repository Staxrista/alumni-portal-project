from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from . import db
from .security import login_required, normalize_email

bp = Blueprint("portal", __name__, url_prefix="/alumni")


def read_profile_form():
    return {
        "full_name": request.form.get("full_name", ""),
        "student_id": request.form.get("student_id", ""),
        "graduation_year": request.form.get("graduation_year", ""),
        "course": request.form.get("course", ""),
        "job_title": request.form.get("job_title", ""),
        "company": request.form.get("company", ""),
        "location": request.form.get("location", ""),
        "linkedin_url": request.form.get("linkedin_url", ""),
        "bio": request.form.get("bio", ""),
        "visibility": request.form.get("visibility", "private"),
    }


def validate_profile(data):
    required = ["full_name", "graduation_year", "course", "bio"]
    for field in required:
        if not str(data.get(field, "")).strip():
            return "Please complete full name, graduation year, course, and profile bio."
    try:
        year = int(data["graduation_year"])
    except ValueError:
        return "Graduation year must be a number."
    if year < 1977 or year > 2035:
        return "Graduation year must be realistic for Mediterranean College alumni."
    if data.get("visibility") not in {"public", "private"}:
        return "Choose a valid profile visibility option."
    return None


@bp.route("/")
def home():
    schools = db.list_schools()
    profiles = db.list_profiles()
    return render_template("portal/home.html", schools=schools, profiles=profiles[:6], stats=db.stats())


@bp.route("/directory")
def directory():
    school_id = request.args.get("school_id", type=int)
    query = request.args.get("q", "").strip()
    profiles = db.list_profiles(school_id=school_id, query=query)
    return render_template("portal/directory.html", schools=db.list_schools(), profiles=profiles, selected_school=school_id, query=query)


@bp.route("/apply", methods=("GET", "POST"))
def apply():
    schools = db.list_schools()
    if request.method == "POST":
        email = normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        school_id = request.form.get("school_id", type=int)
        profile_data = read_profile_form()
        error = None
        if not email or "@" not in email:
            error = "Enter a valid email address."
        elif db.get_user_by_email(email) is not None:
            error = "An account already exists for that email."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif not school_id:
            error = "Choose the Mediterranean College School for this profile."
        else:
            error = validate_profile(profile_data)
        if error:
            flash(error, "error")
            return render_template("portal/apply.html", schools=schools, form=request.form)
        user_id = db.create_user(email, generate_password_hash(password), "applied_alumni")
        profile_data["visibility"] = "private"
        db.create_profile(user_id, school_id, profile_data)
        db.create_application(user_id)
        db.log_event("application_submitted", user_id, user_id, "New alumni application submitted.")
        db.get_db().commit()
        flash("Application submitted. Sign in to track your alumni approval status.", "success")
        return redirect(url_for("auth.login"))
    return render_template("portal/apply.html", schools=schools, form={})


@bp.route("/profile", methods=("GET", "POST"))
@login_required
def profile():
    profile_row = db.get_profile_for_user(g.user["id"])
    application = db.get_application_for_user(g.user["id"])
    schools = db.list_schools()
    if profile_row is None:
        flash("No alumni profile is linked to this account.", "warning")
        if g.user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("portal.apply"))
    if request.method == "POST":
        school_id = request.form.get("school_id", type=int)
        profile_data = read_profile_form()
        if g.user["role"] != "registered_alumni":
            profile_data["visibility"] = "private"
        error = None if school_id else "Choose a school."
        if error is None:
            error = validate_profile(profile_data)
        if error:
            flash(error, "error")
        else:
            db.update_profile(g.user["id"], school_id, profile_data)
            db.log_event("profile_updated", g.user["id"], g.user["id"], "Alumni profile edited.")
            db.get_db().commit()
            flash("Profile updated.", "success")
            return redirect(url_for("portal.profile"))
    return render_template("portal/profile.html", profile=profile_row, application=application, schools=schools)


@bp.route("/status")
@login_required
def status():
    profile_row = db.get_profile_for_user(g.user["id"])
    application = db.get_application_for_user(g.user["id"])
    if profile_row is None:
        flash("No alumni application profile is linked to this account.", "warning")
        return redirect(url_for("portal.home"))
    return render_template("portal/status.html", profile=profile_row, application=application)
