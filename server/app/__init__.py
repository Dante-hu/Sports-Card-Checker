# app/__init__.py
import os
import time
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

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

    # Get allowed origins from environment or use defaults
    allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "").strip()

    if allowed_origins_env:
        # Split comma-separated list from environment
        allowed_origins = [
            origin.strip()
            for origin in allowed_origins_env.split(",")
            if origin.strip()
        ]
    else:
        # Default origins - more permissive but still secure
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",  # Common React dev port
            "https://sportscard-checker.netlify.app",
            "https://*.netlify.app",  # Allow all Netlify subdomains
            "https://sportscard-checker-*.netlify.app",  # Netlify deploy previews
        ]

    print(f"✅ CORS Allowed Origins: {allowed_origins}")

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "allow_headers": [
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                    "Accept",
                    "Origin",
                    "Access-Control-Request-Method",
                    "Access-Control-Request-Headers",
                ],
                "expose_headers": [
                    "Content-Type",
                    "Authorization",
                    "Content-Length",
                    "X-Request-ID",
                ],
                "supports_credentials": True,
                "max_age": 600,  # Cache preflight requests for 10 minutes
            }
        },
        supports_credentials=True,
    )

    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        # Allow credentials
        response.headers.add("Access-Control-Allow-Credentials", "true")

        # If request origin is in allowed list, echo it back
        origin = request.headers.get("Origin")
        if origin and origin in allowed_origins:
            response.headers.add("Access-Control-Allow-Origin", origin)

        return response

    # ============================================
    # END CORS CONFIGURATION
    # ============================================

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
                print(
                    f"🔗 Trying to connect to DB (attempt {attempt}/{max_attempts})..."
                )
                db.create_all()
                print("✅ DB ready and tables created (or already exist).")
                break
            except OperationalError as e:
                print(f"⏳ DB not ready yet: {e}")
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

            print("🔄 Running card importer on startup...")

            env = os.environ.copy()
            env[SKIP_FLAG] = "1"

            subprocess.run(
                [sys.executable, "-m", "scripts.import_cards_from_output"],
                cwd=importer_cwd,
                check=True,
                env=env,
            )
            time.sleep(2)
            print("✅ Card importer finished.")
        except Exception as e:
            print("❌ Import error in create_app:", e)

    return app
