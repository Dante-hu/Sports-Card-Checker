from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import User 
from ..extensions import db 

# Blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/api")

# Schemas
def _validate_signup(data):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return None, {"error": "email and password required"}, 400
    return {"email": email.strip().lower(), "password": password}, None, None

def _validate_login(data):
    return _validate_signup(data)  

# Routes
@auth_bp.post("/signup")
def signup():
    data, err, code = _validate_signup(request.get_json())
    if err:
        return jsonify(err), code

    exists = User.query.filter_by(email=data["email"]).first()
    if exists:
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "email": user.email}), 201

@auth_bp.post("/login")
def login():
    data, err, code = _validate_login(request.get_json())
    if err:
        return jsonify(err), code

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful"}), 200