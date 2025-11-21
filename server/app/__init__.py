from flask import Flask
from .extensions import db
from .models import *  # registers all model classes
from .api.auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()  # create tables
    return app
