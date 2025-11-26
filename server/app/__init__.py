# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .extensions import db
from .models import *  # registers all model classes
from .api.auth import auth_bp
from .api.cards import cards_bp
from .api.sets import sets_bp
from .api.wanted_cards import wanted_cards_bp
from .api.owned_cards import owned_cards_bp
import os


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- SQLite DB in instance/project.db ---
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, "project.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-change-me"

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

    # Ensure tables exist
    with app.app_context():
        db.create_all()

    return app
