from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..models.card import Card
from ..extensions import db
from ..models.set import Set

cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")


def serialize_card(card: Card) -> dict:
    """Helper to keep JSON output consistent."""
    raw_year = card.year
    # If year is a string of digits like "2023", return it as int 2023
    if isinstance(raw_year, str) and raw_year.isdigit():
        year_value = int(raw_year)
    else:
        # For things like "2024-25" or None, just return as-is
        year_value = raw_year
    return {
        "id": card.id,
        "sport": card.sport,
        "year": year_value,
        "brand": card.brand,
        "set_name": card.set_name,
        "card_number": card.card_number,
        "player_name": card.player_name,
        "team": card.team,
        "image_url": card.image_url,
    }


@cards_bp.get("")
def list_cards():
    query = Card.query

    # ----- filters -----
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

    # ----- pagination -----
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    # safety limits
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    if per_page > 100:
        per_page = 100

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = [serialize_card(c) for c in pagination.items]

    return jsonify(
        {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


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


@cards_bp.post("")
def create_card():
    data = request.get_json() or {}

    sport = data.get("sport")
    year = data.get("year")
    brand = data.get("brand")
    set_name = data.get("set_name")
    card_number = data.get("card_number")
    player_name = data.get("player_name")
    team = data.get("team")
    image_url = data.get("image_url")

    # Validate required fields
    missing = [
        field
        for field, value in {
            "sport": sport,
            "year": year,
            "brand": brand,
            "set_name": set_name,
            "card_number": card_number,
            "player_name": player_name,
            "team": team,
        }.items()
        if value in (None, "", [])
    ]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # 🔹 AUTO-CREATE OR FETCH EXISTING SET
    set_obj = Set.query.filter_by(
        sport=sport,
        year=year,
        brand=brand,
        set_name=set_name,
    ).first()

    if not set_obj:
        set_obj = Set(
            sport=sport,
            year=year,
            brand=brand,
            set_name=set_name,
        )
        db.session.add(set_obj)
        # will commit later together

    # 🔹 CREATE THE CARD
    card = Card(
        sport=sport,
        year=year,
        brand=brand,
        set_name=set_name,
        card_number=card_number,
        player_name=player_name,
        team=team,
        image_url=image_url,
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
    card = Card.query.get(card_id)  # Use get() instead of get_or_404()
    if not card:
        return jsonify({"error": "Card not found"}), 404
    
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
    return jsonify(serialize_card(card)), 200