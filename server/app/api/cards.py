from flask import Blueprint, jsonify, request
from ..models.card import Card
from ..models.set import Set
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
            "image_url": c.image_url,
        }
        for c in cards
    ])


@cards_bp.post("/")
def create_card():
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
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    sport = data["sport"]
    year = int(data["year"])
    brand = data["brand"]
    set_name = data["set_name"]

    existing_set = Set.query.filter_by(
        sport=sport,
        year=year,
        brand=brand,
        set_name=set_name,
    ).first()

    if existing_set is None:
        existing_set = Set(
            sport=sport,
            year=year,
            brand=brand,
            set_name=set_name,
        )
        db.session.add(existing_set)

    card = Card(
        sport=sport,
        year=year,
        brand=brand,
        set_name=set_name,
        card_number=data["card_number"],
        player_name=data["player_name"],
        team=data["team"],
        image_url=data.get("image_url"),
    )

    db.session.add(card)
    db.session.commit()

    return jsonify(
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
    ), 201


@cards_bp.delete("/<int:card_id>")
def delete_card(card_id):
    card = Card.query.get(card_id)
    if card is None:
        return jsonify({"error": "Card not found"}), 404

    db.session.delete(card)
    db.session.commit()
    return jsonify({"message": "Card deleted", "id": card_id})


@cards_bp.get("/<int:card_id>")
def get_card(card_id):
    """Return details for a single card by its ID."""
    from app.models.card import Card  # remove this line if Card is already imported at the top

    card = Card.query.get(card_id)
    if not card:
        return jsonify({"error": f"Card with id {card_id} not found"}), 404

    return jsonify(
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
    ), 200
