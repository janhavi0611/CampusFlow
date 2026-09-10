import os
from pathlib import Path

from flask import Flask, redirect, render_template, url_for
from flask_login import LoginManager, current_user

from .extensions import db, migrate
from .models import User
from .routes.auth import auth_bp
from .routes.dashboard import dashboard_bp
from .routes.events import events_bp
from .routes.requests import requests_bp
from .routes.resources import resources_bp


def create_app(config_overrides: dict = None):
    app = Flask(__name__, instance_relative_config=True)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    database_path = Path(app.instance_path) / "app.db"

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", f"sqlite:///{database_path}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(dashboard_bp)

    @app.context_processor
    def inject_current_user():
        return {"current_user": current_user}

    @app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden_error(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app
