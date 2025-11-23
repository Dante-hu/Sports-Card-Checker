from datetime import date
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import OwnedCard, User, Card

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
        "acquired_price": float(owned.acquired_price)
        if owned.acquired_price is not None
        else None,
        "acquired_date": owned.acquired_date.isoformat()
        if owned.acquired_date is not None
        else None,
        "is_for_trade": owned.is_for_trade,
        "notes": owned.notes,
        "created_at": owned.created_at.isoformat()
        if owned.created_at is not None
        else None,
        "card": {
            "id": owned.card.id,
            "sport": owned.card.sport,
            "year": owned.card.year,
            "brand": owned.card.brand,
            "set_name": owned.card.set_name,
            "card_number": owned.card.card_number,
            "player_name": owned.card.player_name,
            "team": owned.card.team,
        }
        if owned.card is not None
        else None,
    }


@owned_cards_bp.get("/")
def list_owned_cards():
    """
    List owned cards.

    Optional query params:
      ?owner_id=1  -> only that user's cards
    """
    owner_id = request.args.get("owner_id", type=int)

    query = OwnedCard.query
    if owner_id is not None:
        query = query.filter_by(owner_id=owner_id)

    owned_cards = query.all()
    return jsonify([owned_card_to_dict(o) for o in owned_cards]), 200


@owned_cards_bp.get("/<int:owned_id>")
def get_owned_card(owned_id: int):
    """
    Get a single owned card by its id.
    """
    owned = OwnedCard.query.get_or_404(owned_id)
    return jsonify(owned_card_to_dict(owned)), 200


@owned_cards_bp.post("/")
def create_owned_card():
    """
    Create or update an owned card.

    Behaviour:
    - If no row exists for (owner_id, card_id) -> create new row.
    - If rows already exist:
        * Merge ALL duplicates into the first row
        * Add the new quantity onto that row
        * Delete the extra duplicate rows
    """
    data = request.get_json() or {}

    owner_id = data.get("owner_id")
    card_id = data.get("card_id")

    if not owner_id or not card_id:
        return jsonify({"error": "owner_id and card_id are required"}), 400

    owner = User.query.get(owner_id)
    card = Card.query.get(card_id)

    if owner is None:
        return jsonify({"error": f"owner_id {owner_id} not found"}), 404
    if card is None:
        return jsonify({"error": f"card_id {card_id} not found"}), 404

    # default quantity = 1 if not provided
    quantity = data.get("quantity", 1)
    if quantity is None:
        quantity = 1

    # 🔍 Get ALL existing owned cards for this owner + card
    existing_rows = (
        OwnedCard.query.filter_by(owner_id=owner_id, card_id=card_id)
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
        # e.g., if you want the latest condition/notes to be saved:
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
        owner_id=owner_id,
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
def delete_owned_card(owned_id: int):
    owned = OwnedCard.query.get_or_404(owned_id)

    owner_id = owned.owner_id
    card_id = owned.card_id

    # Get ALL rows for this owner + card, ordered by id
    rows = (
        OwnedCard.query.filter_by(owner_id=owner_id, card_id=card_id)
        .order_by(OwnedCard.id)
        .all()
    )

    # Use the first row as the main one
    base = rows[0]

    # Merge duplicates into base
    for dup in rows[1:]:
        base.quantity += dup.quantity
        db.session.delete(dup)

    # Now remove ONE copy
    base.quantity -= 1

    if base.quantity <= 0:
        # No copies left → delete completely
        db.session.delete(base)

    db.session.commit()

    return jsonify({"message": "One copy removed."}), 200
