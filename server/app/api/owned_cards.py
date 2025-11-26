from datetime import date
from flask import Blueprint, request, jsonify, g
from ..extensions import db
from ..models import OwnedCard, Card
from .auth import login_required

owned_cards_bp = Blueprint(
    "owned_cards",
    __name__,
    url_prefix="/api/owned-cards",
)


def owned_card_to_dict(owned: OwnedCard) -> dict:
    return {
        "id": owned.id,
        "owner_id": owned.owner_id,
        "card_id": owned.card_id,
        "quantity": owned.quantity,
        "condition": owned.condition,
        "grade": float(owned.grade) if owned.grade is not None else None,
        "acquired_price": (
            float(owned.acquired_price) if owned.acquired_price is not None else None
        ),
        "acquired_date": (
            owned.acquired_date.isoformat() if owned.acquired_date is not None else None
        ),
        "is_for_trade": owned.is_for_trade,
        "notes": owned.notes,
        "created_at": (
            owned.created_at.isoformat() if owned.created_at is not None else None
        ),
        "card": (
            {
                "id": owned.card.id,
                "sport": owned.card.sport,
                "year": owned.card.year,
                "brand": owned.card.brand,
                "set_name": owned.card.set_name,
                "card_number": owned.card.card_number,
                "player_name": owned.card.player_name,
                "team": owned.card.team,
                # 👇👇👇 THIS LINE IS THE FIX
                "image_url": owned.card.image_url,
            }
            if owned.card is not None
            else None
        ),
    }


@owned_cards_bp.get("/")
@login_required
def list_owned_cards():
    """
    List owned cards for the logged-in user only.
    """
    user = g.current_user
    owned_cards = OwnedCard.query.filter_by(owner_id=user.id).all()
    return jsonify([owned_card_to_dict(o) for o in owned_cards]), 200


@owned_cards_bp.get("/<int:owned_id>")
@login_required
def get_owned_card(owned_id: int):
    """
    Get a single owned card by its id, only if it belongs to the logged-in user.
    """
    user = g.current_user
    owned = OwnedCard.query.get_or_404(owned_id)

    if owned.owner_id != user.id:
        # pretend it doesn't exist if it's someone else's
        return jsonify({"error": "owned card not found"}), 404

    return jsonify(owned_card_to_dict(owned)), 200


@owned_cards_bp.post("/")
@login_required
def create_owned_card():
    """
    Create or update an owned card for the logged-in user.

    Behaviour:
    - If no row exists for (owner_id = current user, card_id) -> create new row.
    - If rows already exist:
        * Merge ALL duplicates into the first row
        * Add the new quantity onto that row
        * Delete the extra duplicate rows
    """
    user = g.current_user
    data = request.get_json() or {}

    card_id = data.get("card_id")

    if not card_id:
        return jsonify({"error": "card_id is required"}), 400

    card = Card.query.get(card_id)
    if card is None:
        return jsonify({"error": f"card_id {card_id} not found"}), 404

    # default quantity = 1 if not provided
    quantity = data.get("quantity", 1)
    if quantity is None:
        quantity = 1

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({"error": "quantity must be an integer"}), 400

    if quantity <= 0:
        return jsonify({"error": "quantity must be positive"}), 400

    # 🔍 Get ALL existing owned cards for this user + card
    existing_rows = (
        OwnedCard.query.filter_by(owner_id=user.id, card_id=card_id)
        .order_by(OwnedCard.id)
        .all()
    )

    if existing_rows:
        # Use the first row as the "main" one
        base = existing_rows[0]

        # Merge any duplicates into base
        for dup in existing_rows[1:]:
            base.quantity += dup.quantity
            db.session.delete(dup)

        # Now add the new quantity as well
        base.quantity += quantity

        # Optional: update some fields from the incoming data
        if "condition" in data:
            base.condition = data["condition"]
        if "grade" in data:
            base.grade = data["grade"]
        if "acquired_price" in data:
            base.acquired_price = data["acquired_price"]
        if "acquired_date" in data:
            acquired_date_str = data.get("acquired_date")
            if acquired_date_str:
                try:
                    base.acquired_date = date.fromisoformat(acquired_date_str)
                except ValueError:
                    return jsonify({"error": "acquired_date must be YYYY-MM-DD"}), 400
        if "is_for_trade" in data:
            base.is_for_trade = bool(data["is_for_trade"])
        if "notes" in data:
            base.notes = data["notes"]

        db.session.commit()
        return jsonify(owned_card_to_dict(base)), 200

    # No existing entry → create new one
    condition = data.get("condition", "Unknown")
    grade = data.get("grade")  # can be None
    acquired_price = data.get("acquired_price")  # can be None
    acquired_date_str = data.get("acquired_date")  # "YYYY-MM-DD" or None
    is_for_trade = bool(data.get("is_for_trade", False))
    notes = data.get("notes")

    acquired_date = None
    if acquired_date_str:
        try:
            acquired_date = date.fromisoformat(acquired_date_str)
        except ValueError:
            return jsonify({"error": "acquired_date must be YYYY-MM-DD"}), 400

    owned = OwnedCard(
        owner_id=user.id,
        card_id=card_id,
        quantity=quantity,
        condition=condition,
        grade=grade,
        acquired_price=acquired_price,
        acquired_date=acquired_date,
        is_for_trade=is_for_trade,
        notes=notes,
    )

    db.session.add(owned)
    db.session.commit()

    return jsonify(owned_card_to_dict(owned)), 201


@owned_cards_bp.delete("/<int:owned_id>")
@login_required
def delete_owned_card(owned_id: int):
    user = g.current_user

    owned = OwnedCard.query.get_or_404(owned_id)
    if owned.owner_id != user.id:
        return jsonify({"error": "owned card not found"}), 404

    owner_id = owned.owner_id
    card_id = owned.card_id

    # Merge duplicates for this user + card into one row
    rows = (
        OwnedCard.query.filter_by(owner_id=owner_id, card_id=card_id)
        .order_by(OwnedCard.id)
        .all()
    )

    if not rows:
        return jsonify({"error": "owned card not found"}), 404

    base = rows[0]

    for dup in rows[1:]:
        base.quantity += dup.quantity
        db.session.delete(dup)

    # NEW: how many copies to remove
    count = request.args.get("count", 1, type=int)
    if count < 1:
        count = 1
    if count > base.quantity:
        count = base.quantity

    base.quantity -= count

    if base.quantity <= 0:
        db.session.delete(base)
        db.session.commit()
        return jsonify({"deleted": True, "remaining": 0}), 200

    db.session.commit()
    return jsonify(
        {
            "deleted": False,
            "remaining": base.quantity,
            "owned": owned_card_to_dict(base),
        }
    ), 200


@owned_cards_bp.post("/by-name")
@login_required
def add_owned_card_by_name():
    user = g.current_user
    data = request.get_json() or {}

    player_name = data.get("player_name")
    year = data.get("year")
    brand = data.get("brand")

    if not player_name or not year or not brand:
        return jsonify({"error": "player_name, year, and brand are required"}), 400

    # Find the exact card
    card = Card.query.filter_by(player_name=player_name, year=year, brand=brand).first()

    if not card:
        return (
            jsonify({"error": f"No card found for {year} {brand} {player_name}"}),
            404,
        )

    quantity = int(data.get("quantity", 1))
    condition = data.get("condition", "Mint")

    # Check if user already owns it
    existing = OwnedCard.query.filter_by(
        owner_id=user.id, card_id=card.id, condition=condition
    ).first()

    if existing:
        existing.quantity += quantity
        db.session.commit()
        return jsonify(owned_card_to_dict(existing)), 200

    # Otherwise create new entry
    owned = OwnedCard(
        owner_id=user.id, card_id=card.id, quantity=quantity, condition=condition
    )

    db.session.add(owned)
    db.session.commit()
    return jsonify(owned_card_to_dict(owned)), 201
