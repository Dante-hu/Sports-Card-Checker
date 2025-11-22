from flask import Blueprint, jsonify, request
from ..models.card import Card
from ..extensions import db


cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")


@cards_bp.get("/")
def list_cards():
    cards = Card.query.all()
    return jsonify([
        {
            "id": c.id,
            "sport": c.sport,
            "year": c.year,
            "brand": c.brand,
            "set_name": c.set_name,
            "card_number": c.card_number,
            "player_name": c.player_name,
            "team": c.team,
        }
        for c in cards
    ])

@cards_bp.post("/")
def create_card():
    """Create a real card from JSON data."""
    data = request.get_json() or {}

    required_fields = [
        "sport",
        "year",
        "brand",
        "set_name",
        "card_number",
        "player_name",
        "team",
    ]

    missing = [field for field in required_fields if field not in data]
    if missing:
        return (
            jsonify({"error": f"Missing fields: {', '.join(missing)}"}),
            400,
        )

    #creates the Card object
    card = Card(
        sport=data["sport"],
        year=int(data["year"]),
        brand=data["brand"],
        set_name=data["set_name"],
        card_number=data["card_number"],
        player_name=data["player_name"],
        team=data["team"],
        image_url=data.get("image_url"),  # optional
    )

    db.session.add(card)
    db.session.commit()

    return (
        jsonify(
            {
                "id": card.id,
                "sport": card.sport,
                "year": card.year,
                "brand": card.brand,
                "set_name": card.set_name,
                "card_number": card.card_number,
                "player_name": card.player_name,
                "team": card.team,
            }
        ),
        201,
    )


