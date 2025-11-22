from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.wanted_card import WantedCard
from app.models.card import Card
from app.models.User import User  # keep to match your project

wanted_cards_bp = Blueprint("wanted_cards", __name__, url_prefix="/api/wanted")


@wanted_cards_bp.get("/")
def get_wanted_cards():
    """Return all wanted cards (all users)."""
    items = WantedCard.query.all()
    return jsonify([item.to_dict() for item in items]), 200


@wanted_cards_bp.get("/user/<int:user_id>")
def get_wanted_cards_for_user(user_id):
    """Return wantlist items for a specific user."""
    items = WantedCard.query.filter_by(user_id=user_id).all()
    return jsonify([item.to_dict() for item in items]), 200


@wanted_cards_bp.post("/")
def add_wanted_card():
    """Add a card to a user's wantlist by card_id or player_name."""
    data = request.get_json() or {}

    user_id = data.get("user_id")
    card_id = data.get("card_id")
    notes = data.get("notes")
    player_name = data.get("player_name")  # allows adding by name

    # Validate required user
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Validate user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": f"User with id {user_id} not found"}), 404

    # If no card_id is provided, try to find the card by player_name
    if not card_id and player_name:
        card_obj = Card.query.filter_by(player_name=player_name).first()
        if not card_obj:
            return jsonify(
                {"error": f"No card found with player_name '{player_name}'"}
            ), 404
        card_id = card_obj.id

    # If still no card_id, we can't proceed
    if not card_id:
        return jsonify(
            {"error": "Either card_id or player_name is required"}
        ), 400

    # Validate card exists (in case card_id was sent directly)
    card = Card.query.get(card_id)
    if not card:
        return jsonify({"error": f"Card with id {card_id} not found"}), 404

    # Prevent duplicates (same user + same card)
    existing_item = WantedCard.query.filter_by(
        user_id=user_id, card_id=card_id
    ).first()
    if existing_item:
        return (
            jsonify(
                {
                    "error": "Card already in wantlist for this user",
                    "item": existing_item.to_dict(),
                }
            ),
            409,
        )

    # Create new wanted card entry
    new_item = WantedCard(
        user_id=user_id,
        card_id=card_id,
        notes=notes,
    )

    db.session.add(new_item)
    db.session.commit()

    return jsonify(new_item.to_dict()), 201


@wanted_cards_bp.delete("/<int:item_id>")
def delete_wanted_card(item_id):
    """Delete a wantlist item by its ID."""
    item = WantedCard.query.get(item_id)

    if not item:
        return jsonify({"error": "Wanted card not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Deleted"}), 200


@wanted_cards_bp.delete("/by_name")
def delete_wanted_card_by_name():
    """
    Delete a wanted card by user_id + player_name.
    Example: /api/wanted/by_name?user_id=1&player_name=Connor%20Bedard
    """
    user_id = request.args.get("user_id", type=int)
    player_name = request.args.get("player_name", type=str)

    if not user_id or not player_name:
        return jsonify({"error": "user_id and player_name are required"}), 400

    # Find the user
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": f"User with id {user_id} not found"}), 404

    # Find the card by player_name
    card = Card.query.filter_by(player_name=player_name).first()
    if not card:
        return jsonify(
            {"error": f"No card found with player_name '{player_name}'"}
        ), 404

    # Find the wanted card entry
    item = WantedCard.query.filter_by(user_id=user_id, card_id=card.id).first()
    if not item:
        return jsonify(
            {
                "error": "No wanted card found for this user and player_name",
                "user_id": user_id,
                "player_name": player_name,
            }
        ), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Deleted wanted card for this user and player"}), 200
