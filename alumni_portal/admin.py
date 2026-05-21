import sqlite3

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from . import db
from .security import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@role_required("admin")
def dashboard():
    return render_template(
        "admin/dashboard.html",
        pending=db.list_applications("pending"),
        reviewed=db.list_applications(),
        schools=db.list_schools(),
        stats=db.stats(),
    )


@bp.route("/applications/<int:application_id>/approve", methods=("POST",))
@role_required("admin")
def approve(application_id):
    notes = request.form.get("admin_notes", "Approved by alumni office.")
    if db.review_application(application_id, "approved", g.user["id"], notes):
        flash("Application approved. The applicant is now a Registered Alumni user.", "success")
    else:
        flash("Application not found.", "error")
    return redirect(url_for("admin.dashboard"))


@bp.route("/applications/<int:application_id>/reject", methods=("POST",))
@role_required("admin")
def reject(application_id):
    notes = request.form.get("admin_notes", "Rejected by alumni office.")
    if db.review_application(application_id, "rejected", g.user["id"], notes):
        flash("Application rejected and kept private.", "warning")
    else:
        flash("Application not found.", "error")
    return redirect(url_for("admin.dashboard"))


@bp.route("/schools", methods=("POST",))
@role_required("admin")
def add_school():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not name or not description:
        flash("School name and description are required.", "error")
        return redirect(url_for("admin.dashboard"))
    try:
        db.add_school(name, description)
        db.log_event("school_created", g.user["id"], None, name)
        db.get_db().commit()
        flash("School added.", "success")
    except sqlite3.IntegrityError:
        flash("A school with that name already exists.", "error")
    return redirect(url_for("admin.dashboard"))
