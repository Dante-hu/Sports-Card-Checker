from flask import Blueprint, request, jsonify, g
from ..extensions import db
from ..models.wanted_card import WantedCard
from ..models.card import Card
from .auth import login_required  # use the login_required we made earlier

wanted_cards_bp = Blueprint("wanted_cards", __name__, url_prefix="/api/wanted")


def wanted_to_dict(item: WantedCard) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "card_id": item.card_id,
        "notes": item.notes,
        "created_at": (
            item.created_at.isoformat()
            if getattr(item, "created_at", None) is not None
            else None
        ),
        "card": (
            {
                "id": item.card.id,
                "sport": item.card.sport,
                "year": item.card.year,
                "brand": item.card.brand,
                "set_name": item.card.set_name,
                "card_number": item.card.card_number,
                "player_name": item.card.player_name,
                "team": item.card.team,
                "image_url": item.card.image_url,
            }
            if item.card is not None
            else None
        ),
    }


@wanted_cards_bp.get("")
@login_required
def get_wanted_cards():
    """Return wantlist items for the logged-in user only."""
    user = g.current_user
    items = WantedCard.query.filter_by(user_id=user.id).all()
    return jsonify([wanted_to_dict(item) for item in items]), 200


@wanted_cards_bp.post("")
@login_required
def add_wanted_card():
    user = g.current_user
    data = request.get_json() or {}

    card_id = data.get("card_id")
    player_name = data.get("player_name")
    notes = data.get("notes")

    # If no card_id is provided, try to find the card by player_name
    if not card_id and player_name:
        card_obj = Card.query.filter_by(player_name=player_name).first()
        if not card_obj:
            return (
                jsonify({"error": f"No card found with player_name '{player_name}'"}),
                404,
            )
        card_id = card_obj.id

    # If still no card_id, we can't proceed
    if not card_id:
        return jsonify({"error": "Either card_id or player_name is required"}), 400

    # Validate card exists (in case card_id was sent directly)
    card = Card.query.get(card_id)
    if not card:
        return jsonify({"error": f"Card with id {card_id} not found"}), 404

    # Prevent duplicates (same user + same card)
    existing_item = WantedCard.query.filter_by(user_id=user.id, card_id=card_id).first()
    if existing_item:
        # If it's already there, optionally update notes, but don't duplicate
        if "notes" in data:
            existing_item.notes = notes
            db.session.commit()
        return (
            jsonify(
                {
                    "error": "Card already in wantlist for this user",
                    "item": wanted_to_dict(existing_item),
                }
            ),
            409,
        )

    # Create new wanted card entry
    new_item = WantedCard(
        user_id=user.id,
        card_id=card_id,
        notes=notes,
    )

    db.session.add(new_item)
    db.session.commit()

    return jsonify(wanted_to_dict(new_item)), 201


@wanted_cards_bp.delete("/<int:item_id>")
@login_required
def delete_wanted_card(item_id):
    """Delete a wantlist item by its ID, only if it belongs to the logged-in user."""
    user = g.current_user
    item = WantedCard.query.get(item_id)

    if not item or item.user_id != user.id:
        return jsonify({"error": "Wanted card not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Deleted"}), 200


@wanted_cards_bp.delete("/by_name")
@login_required
def delete_wanted_card_by_name():
    """
    Delete a wanted card by player_name + year + brand for the logged-in user.

    Example:
      DELETE /api/wanted/by_name?player_name=Wayne%20Gretzky&year=1998&brand=O-Pee-Chee
    """
    user = g.current_user

    player_name = request.args.get("player_name", type=str)
    year = request.args.get("year", type=int)
    brand = request.args.get("brand", type=str)

    if not player_name or year is None or not brand:
        return jsonify({"error": "player_name, year, and brand are required"}), 400

    # Find the exact card
    card = Card.query.filter_by(
        player_name=player_name,
        year=year,
        brand=brand,
    ).first()

    if not card:
        return (
            jsonify({"error": f"No card found for {year} {brand} {player_name}"}),
            404,
        )

    # Find the wanted card entry for this user + card
    item = WantedCard.query.filter_by(user_id=user.id, card_id=card.id).first()
    if not item:
        return (
            jsonify(
                {
                    "error": "No wanted card found for this user and that card",
                    "player_name": player_name,
                    "year": year,
                    "brand": brand,
                }
            ),
            404,
        )

    db.session.delete(item)
    db.session.commit()

    return (
        jsonify({"message": "Deleted wanted card for this user and player/year/brand"}),
        200,
    )


@wanted_cards_bp.post("/by_name")
@login_required
def add_wanted_card_by_name():
    """
    Add a wanted card for the LOGGED-IN user using player_name + year + brand.

    Expected JSON:
    {
      "player_name": "Wayne Gretzky",
      "year": 1998,
      "brand": "O-Pee-Chee",
      "notes": "1998 OPC Gretzky"   # optional
    }
    """
    user = g.current_user
    data = request.get_json() or {}

    player_name = data.get("player_name")
    year = data.get("year")
    brand = data.get("brand")
    notes = data.get("notes")

    if not player_name or year is None or not brand:
        return jsonify({"error": "player_name, year, and brand are required"}), 400

    # make sure year is an integer
    try:
        year = int(year)
    except (TypeError, ValueError):
        return jsonify({"error": "year must be an integer"}), 400

    # Find the exact card
    card = Card.query.filter_by(
        player_name=player_name,
        year=year,
        brand=brand,
    ).first()

    if not card:
        return (
            jsonify({"error": f"No card found for {year} {brand} {player_name}"}),
            404,
        )

    # Prevent duplicates (same user + same card)
    existing_item = WantedCard.query.filter_by(user_id=user.id, card_id=card.id).first()
    if existing_item:
        # optionally update notes if provided
        if notes is not None:
            existing_item.notes = notes
            db.session.commit()
        return (
            jsonify(
                {
                    "error": "Card already in wantlist for this user",
                    "item": wanted_to_dict(existing_item),
                }
            ),
            409,
        )

    # Create new wanted card
    new_item = WantedCard(
        user_id=user.id,
        card_id=card.id,
        notes=notes,
    )
    db.session.add(new_item)
    db.session.commit()

    return jsonify(wanted_to_dict(new_item)), 201
