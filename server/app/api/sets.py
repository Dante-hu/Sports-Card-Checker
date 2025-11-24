from flask import Blueprint, jsonify
from ..models.set import Set
from ..extensions import db
from ..models.card import Card

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


@sets_bp.get("/")
def list_sets():
    sets = Set.query.all()
    return jsonify(
        [
            {
                "id": s.id,
                "sport": s.sport,
                "year": s.year,
                "brand": s.brand,
                "set_name": s.set_name,
            }
            for s in sets
        ]
    )


@sets_bp.get("/<int:set_id>/cards")
def get_cards_for_set(set_id):
    """
    Return all cards belonging to a specific set, identified by set_id.
    We match cards using the set's sport, year, brand, and set_name.
    """
    # Find the set
    set_obj = Set.query.get(set_id)
    if not set_obj:
        return jsonify({"error": f"Set with id {set_id} not found"}), 404

    # Filter cards that belong to this set
    cards = Card.query.filter_by(
        sport=set_obj.sport,
        year=set_obj.year,
        brand=set_obj.brand,
        set_name=set_obj.set_name,
    ).all()

    # If your Card doesn't have to_dict(), we can build a minimal dict instead
    result = []
    for card in cards:
        if hasattr(card, "to_dict"):
            result.append(card.to_dict())
        else:
            result.append(
                {
                    "id": card.id,
                    "sport": card.sport,
                    "year": card.year,
                    "brand": card.brand,
                    "set_name": card.set_name,
                    "card_number": card.card_number,
                    "player_name": card.player_name,
                    "team": card.team,
                    "image_url": card.image_url,
                }
            )

    return jsonify(result), 200


@sets_bp.get("/<int:set_id>")
def get_set(set_id):
    s = Set.query.get(set_id)
    if not s:
        return jsonify({"error": f"Set with id {set_id} not found"}), 404

    return (
        jsonify(
            {
                "id": s.id,
                "sport": s.sport,
                "year": s.year,
                "brand": s.brand,
                "set_name": s.set_name,
            }
        ),
        200,
    )
