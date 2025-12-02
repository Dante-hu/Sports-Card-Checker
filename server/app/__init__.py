# app/__init__.py
import os
import time  # ⬅ add this
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError  # ⬅ add this

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

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ]
            }
        },
        supports_credentials=True,
    )

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
                    print(
                        "❌ Could not connect to DB after several attempts, giving up."
                    )
                    raise
                time.sleep(delay)

    # ----------------------------------------
    # Run importer automatically on server start (unchanged)
    # ----------------------------------------
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
