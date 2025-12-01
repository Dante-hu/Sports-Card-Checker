# app/__init__.py
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

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
    # Local Postgres default
    DEFAULT_LOCAL_DB = "postgresql://postgres:postgres123@localhost:5433/sports_card_checker"
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

    # Ensure tables exist
    with app.app_context():
        db.create_all()

    return app
