from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..models.card import Card
from ..extensions import db

cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")


def serialize_card(card: Card) -> dict:
    """Helper to keep JSON output consistent."""
    return {
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


@cards_bp.get("/")
def list_cards():
    """
    List cards, with optional filters:

    /api/cards/
    /api/cards/?player=Bedard
    /api/cards/?team=Leafs
    /api/cards/?sport=Hockey&year=2023
    /api/cards/?brand=Upper%20Deck
    /api/cards/?set=Series%201
    /api/cards/?q=Bedard   (search in player/set/team/brand)
    """
    query = Card.query

    sport = request.args.get("sport")
    year = request.args.get("year", type=int)
    brand = request.args.get("brand")
    set_name = request.args.get("set")
    player = request.args.get("player")
    team = request.args.get("team")
    q = request.args.get("q")

    if sport:
        query = query.filter(Card.sport.ilike(f"%{sport}%"))
    if year is not None:
        query = query.filter(Card.year == year)
    if brand:
        query = query.filter(Card.brand.ilike(f"%{brand}%"))
    if set_name:
        query = query.filter(Card.set_name.ilike(f"%{set_name}%"))
    if player:
        query = query.filter(Card.player_name.ilike(f"%{player}%"))
    if team:
        query = query.filter(Card.team.ilike(f"%{team}%"))
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Card.player_name.ilike(like),
                Card.team.ilike(like),
                Card.brand.ilike(like),
                Card.set_name.ilike(like),
            )
        )

    cards = query.all()
    return jsonify([serialize_card(c) for c in cards])


@cards_bp.post("/sample")
def create_sample_card():
    """Create a hard-coded sample card (useful for quick testing)."""
    card = Card(
        sport="Hockey",
        year=2023,
        brand="Upper Deck",
        set_name="Series 1",
        card_number="201",
        player_name="Connor Bedard",
        team="Chicago Blackhawks",
        image_url=None,
    )
    db.session.add(card)
    db.session.commit()
    return jsonify(serialize_card(card)), 201


@cards_bp.post("/")
def create_card():
    """Create a new card from JSON body."""
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
    missing = [f for f in required_fields if f not in data]
    if missing:
        return (
            jsonify({"error": f"Missing fields: {', '.join(missing)}"}),
            400,
        )

    try:
        year = int(data["year"])
    except (TypeError, ValueError):
        return jsonify({"error": "year must be an integer"}), 400

    card = Card(
        sport=data["sport"],
        year=year,
        brand=data["brand"],
        set_name=data["set_name"],
        card_number=data["card_number"],
        player_name=data["player_name"],
        team=data["team"],
        image_url=data.get("image_url"),
    )
    db.session.add(card)
    db.session.commit()
    return jsonify(serialize_card(card)), 201


@cards_bp.route("/<int:card_id>", methods=["PATCH", "PUT"])
def update_card(card_id: int):
    """
    Update an existing card.

    PATCH /api/cards/1
    PUT   /api/cards/1

    Body can include any of:
    sport, year, brand, set_name, card_number, player_name, team, image_url
    """
    card = Card.query.get_or_404(card_id)
    data = request.get_json() or {}

    updatable_fields = [
        "sport",
        "year",
        "brand",
        "set_name",
        "card_number",
        "player_name",
        "team",
        "image_url",
    ]

    for field in updatable_fields:
        if field in data:
            if field == "year":
                try:
                    value = int(data["year"])
                except (TypeError, ValueError):
                    return jsonify({"error": "year must be an integer"}), 400
                setattr(card, "year", value)
            else:
                setattr(card, field, data[field])

    db.session.commit()
    return jsonify(serialize_card(card))
