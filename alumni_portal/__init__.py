import os
from pathlib import Path

from flask import Flask, flash, g, redirect, request, session, url_for

from . import admin, auth, db, portal


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev-change-me",
        DATABASE=os.path.join(app.instance_path, "alumni_portal.sqlite"),
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(db.close_db)

    with app.app_context():
        db.init_db()

    @app.before_request
    def load_current_user():
        g.user = None
        user_id = session.get("user_id")
        if user_id is not None:
            g.user = db.get_user_by_id(user_id)
            if g.user is None:
                session.clear()
                flash("Your session expired. Please sign in again.", "warning")
                return redirect(url_for("auth.login", next=request.path))
        return None

    @app.context_processor
    def inject_globals():
        return {
            "current_user": g.get("user"),
            "role_labels": {
                "admin": "Administrative",
                "registered_alumni": "Registered Alumni",
                "applied_alumni": "Applied Alumni",
            },
        }

    @app.route("/")
    def index():
        return redirect(url_for("portal.home"))

    app.register_blueprint(auth.bp)
    app.register_blueprint(portal.bp)
    app.register_blueprint(admin.bp)
    return app
