import os
import time
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError
from datetime import timedelta

from .extensions import db
from .models import *  # registers all model classes
from .api.auth import auth_bp
from .api.cards import cards_bp
from .api.sets import sets_bp
from .api.wanted_cards import wanted_cards_bp
from .api.owned_cards import owned_cards_bp
from .api.ebay import ebay_bp

load_dotenv()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # DATABASE CONFIG
    DEFAULT_LOCAL_DB = (
        "postgresql://postgres:postgres123@localhost:5433/sports_card_checker"
    )
    db_url = os.environ.get("DATABASE_URL", DEFAULT_LOCAL_DB)

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # These work with Flask's built-in session
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_NAME"] = "sports_card_session"
    app.config["SESSION_COOKIE_SECURE"] = True  # True for HTTPS
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "None"  # Required for cross-domain

    # Initialize CORS
    CORS(app, supports_credentials=True)

    # Handle OPTIONS requests (preflight) for all routes
    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            origin = request.headers.get("Origin")
            response = app.make_default_options_response()

            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin

            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With"
            )
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "600"
            return response

    # Add CORS headers to all responses
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")

        if origin:
            # Allow Netlify and localhost
            if (
                ".netlify.app" in origin
                or "localhost" in origin
                or "127.0.0.1" in origin
            ):
                response.headers["Access-Control-Allow-Origin"] = origin
            else:
                print(f" Request from unexpected origin: {origin}")

        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(sets_bp)
    app.register_blueprint(wanted_cards_bp)
    app.register_blueprint(owned_cards_bp)
    app.register_blueprint(ebay_bp)

    # Ensure tables exist, with retries so Docker Compose doesn't crash
    with app.app_context():
        max_attempts = 10
        delay = 2  # seconds

        for attempt in range(1, max_attempts + 1):
            try:
                print(f" Trying to connect to DB (attempt {attempt}/{max_attempts})...")
                db.create_all()
                print(" DB ready and tables created (or already exist).")
                break
            except OperationalError as e:
                print(f" DB not ready yet: {e}")
                if attempt == max_attempts:
                    print(" Could not connect to DB after several attempts, giving up.")
                    raise
                time.sleep(delay)

    # run importer on startup
    SKIP_FLAG = "SKIP_IMPORTER"

    if os.environ.get(SKIP_FLAG) != "1":
        try:
            import subprocess
            import sys

            importer_cwd = os.path.join(app.root_path, "..")

            print(" Running card importer on startup...")

            env = os.environ.copy()
            env[SKIP_FLAG] = "1"

            subprocess.run(
                [sys.executable, "-m", "scripts.import_cards_from_output"],
                cwd=importer_cwd,
                check=True,
                env=env,
            )
            time.sleep(2)
            print(" Card importer finished.")
        except Exception as e:
            print(" Import error in create_app:", e)

    return app
