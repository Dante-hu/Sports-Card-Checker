from flask import Blueprint, request, jsonify, session, g
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

from ..models import User, OwnedCard, WantedCard, Card
from ..extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


def _validate_signup(data):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return None, {"error": "email and password required"}, 400
    # keep your lowercasing + stripping
    return {"email": email.strip().lower(), "password": password}, None, None


def _validate_login(data):
    # same rules as signup (email + password required)
    return _validate_signup(data)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "authentication required"}), 401

        user = User.query.get(user_id)
        if not user:
            # session has invalid user_id, clear it
            session.pop("user_id", None)
            return jsonify({"error": "invalid session"}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return wrapper


# Routes
@auth_bp.post("/signup")
def signup():
    # NOTE: we grab the raw body FIRST so we can use security_question too
    raw_data = request.get_json() or {}
    data, err, code = _validate_signup(raw_data)
    if err:
        return jsonify(err), code

    exists = User.query.filter_by(email=data["email"]).first()
    if exists:
        return jsonify({"error": "Email already registered"}), 409

    # NEW: security question + answer are optional at signup
    security_question = (raw_data.get("security_question") or "").strip()
    security_answer = (raw_data.get("security_answer") or "").strip()

    user = User(
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
    )

    if security_question and security_answer:
        user.security_question = security_question
        user.set_security_answer(security_answer)

    db.session.add(user)
    db.session.commit()

    # log in right after signup
    session["user_id"] = user.id

    return jsonify({"id": user.id, "email": user.email}), 201


@auth_bp.post("/login")
def login():
    data, err, code = _validate_login(request.get_json() or {})
    if err:
        return jsonify(err), code

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    # store user_id in session
    session["user_id"] = user.id

    return (
        jsonify({"message": "Login successful", "id": user.id, "email": user.email}),
        200,
    )


@auth_bp.post("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "logged out"}), 200


@auth_bp.get("/me")
@login_required
def me():
    user = g.current_user
    return jsonify({"id": user.id, "email": user.email}), 200


@auth_bp.get("/me/summary")
@login_required
def me_summary():
    """
    Return a summary of the logged-in user's collection and wantlist,
    including per-set progress like 'owned / total in set'.
    """
    user = g.current_user

    # ----- Owned cards -----
    owned_q = OwnedCard.query.filter_by(owner_id=user.id).all()
    total_owned_unique = len(owned_q)
    total_owned_quantity = sum(o.quantity for o in owned_q)

    # Breakdown by sport (unique owned cards per sport)
    owned_by_sport = {}

    # Per-set progress
    # key = "2023 Upper Deck Series 1"
    sets_summary = {}

    for oc in owned_q:
        card = oc.card
        if not card:
            continue

        # sport breakdown
        sport = card.sport or "Unknown"
        owned_by_sport[sport] = owned_by_sport.get(sport, 0) + 1

        # set label (year + brand + set_name)
        set_label = f"{card.year} {card.brand} {card.set_name}"

        if set_label not in sets_summary:
            # how many cards exist in this set in the cards table?
            total_in_set = Card.query.filter_by(
                sport=card.sport,
                year=card.year,
                brand=card.brand,
                set_name=card.set_name,
            ).count()

            sets_summary[set_label] = {
                "set_label": set_label,
                "owned_unique": 0,
                "total_in_set": total_in_set,
                # this will be like "3/50"
                "progress": None,
            }

        entry = sets_summary[set_label]
        entry["owned_unique"] += 1

        # build the "owned/total" string (blank/blank style)
        if entry["total_in_set"] > 0:
            entry["progress"] = f"{entry['owned_unique']}/{entry['total_in_set']}"
        else:
            # unknown total -> "3/?"
            entry["progress"] = f"{entry['owned_unique']}/?"

    # ----- Wanted cards -----
    wanted_q = WantedCard.query.filter_by(user_id=user.id).all()
    total_wanted = len(wanted_q)

    return (
        jsonify(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
                "owned": {
                    "total_unique_cards": total_owned_unique,
                    "total_quantity": total_owned_quantity,
                    "by_sport": owned_by_sport,
                },
                "wanted": {
                    "total_wanted_cards": total_wanted,
                },
                "sets": list(sets_summary.values()),
            }
        ),
        200,
    )


# -----------------------------
# NEW: Set / change security question (must be logged in)
# -----------------------------
@auth_bp.post("/security-question")
@login_required
def set_security_question():
    """
    Allow the logged-in user to set or update their security question + answer.
    Body: { "question": "...", "answer": "..." }
    """
    user = g.current_user
    data = request.get_json() or {}

    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()

    if not question or not answer:
        return jsonify({"error": "question and answer are required"}), 400

    user.security_question = question
    user.set_security_answer(answer)

    db.session.commit()

    return jsonify({"message": "Security question updated"}), 200


# -----------------------------
# NEW: Forgot password - get security question by email
# -----------------------------
@auth_bp.post("/forgot-password")
def forgot_password():
    """
    Step 1 of reset: user gives email, we return the security question
    (if it exists) WITHOUT exposing the answer.
    Body: { "email": "..." }
    """
    data = request.get_json() or {}
    raw_email = data.get("email")
    if not raw_email:
        return jsonify({"error": "email is required"}), 400

    email = raw_email.strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user or not user.security_question:
        return (
            jsonify(
                {
                    "error": "No security question set for this account or account not found"
                }
            ),
            404,
        )

    return (
        jsonify(
            {
                "email": email,
                "security_question": user.security_question,
            }
        ),
        200,
    )


# -----------------------------
# NEW: Reset password using security answer
# -----------------------------
@auth_bp.post("/reset-password")
def reset_password_with_security_answer():
    """
    Step 2 of reset: user provides email, security answer, and new password.
    Body: { "email": "...", "answer": "...", "new_password": "..." }
    """
    data = request.get_json() or {}

    raw_email = data.get("email")
    answer = data.get("answer")
    new_password = data.get("new_password")

    if not raw_email or not answer or not new_password:
        return (
            jsonify(
                {
                    "error": "email, answer, and new_password are all required",
                }
            ),
            400,
        )

    email = raw_email.strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user or not user.security_question or not user.security_answer_hash:
        return jsonify({"error": "Unable to reset password for this account"}), 400

    if not user.check_security_answer(answer):
        return jsonify({"error": "Incorrect security answer"}), 401

    # update password
    user.set_password(new_password)
    db.session.commit()

    # Optional: log them in immediately:
    session["user_id"] = user.id

    return jsonify({"message": "Password reset successful"}), 200
