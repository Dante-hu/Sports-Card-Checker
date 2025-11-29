from flask import Blueprint, jsonify, request
import os
import requests
from sqlalchemy import or_
from ..models.card import Card
from ..extensions import db
from ..models.set import Set

cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")


def serialize_card(card: Card) -> dict:
    """Helper to keep JSON output consistent."""
    raw_year = card.year
    if isinstance(raw_year, str) and raw_year.isdigit():
        year_value = int(raw_year)
    else:
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


@cards_bp.get("/")
def list_cards():
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

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

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
    data = request.get_json() or {}

    sport = data.get("sport")
    year = data.get("year")
    brand = data.get("brand")
    set_name = data.get("set_name")
    card_number = data.get("card_number")
    player_name = data.get("player_name")
    team = data.get("team")
    image_url = data.get("image_url")

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


# ----------------------------
# STRICT eBay auto-image logic
# ----------------------------

def build_ebay_query_from_card(card: Card) -> str:
    parts = []
    if card.year:
        parts.append(str(card.year))
    if card.brand:
        parts.append(card.brand)
    if card.set_name:
        parts.append(card.set_name)
    if card.player_name:
        parts.append(card.player_name)
    if card.card_number is not None:
        parts.append(f"#{card.card_number}")
    return " ".join(parts).strip()


@cards_bp.post("/<int:card_id>/auto-image")
def auto_fill_card_image(card_id: int):
    """
    Try to automatically fill card.image_url using the first eBay search result.

    POST /api/cards/<card_id>/auto-image
    """
    card = Card.query.get(card_id)
    if not card:
        return jsonify({"error": "Card not found"}), 404

    query = build_ebay_query_from_card(card)
    if not query:
        return jsonify({"error": "Cannot build search query for this card"}), 400

    token = os.environ.get("EBAY_OAUTH_TOKEN")
    marketplace = os.environ.get("EBAY_MARKETPLACE_ID", "EBAY_CA")

    # If no token, just return the card unchanged
    if not token:
        return jsonify(serialize_card(card)), 200

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace,
        "Content-Type": "application/json",
    }
    params = {
        "q": query,
        "limit": 1,  # just grab the first match
    }

    try:
        resp = requests.get(
            "https://api.ebay.com/buy/browse/v1/item_summary/search",
            headers=headers,
            params=params,
            timeout=10,
        )
    except requests.RequestException as exc:
        # Network / connection error -> just log and return card unchanged
        print("eBay auto-image request error:", exc)
        return jsonify(serialize_card(card)), 200

    # If eBay returns non-200 (e.g. 401 Unauthorized), don't blow up
    if resp.status_code != 200:
        print("eBay auto-image non-200:", resp.status_code, resp.text[:200])
        return jsonify(serialize_card(card)), 200

    data = resp.json()
    items = data.get("itemSummaries") or []
    if not items:
        # nothing found, keep card as-is
        return jsonify(serialize_card(card)), 200

    first = items[0]
    image_url = (
        first.get("image", {}).get("imageUrl")
        or (first.get("thumbnailImages") or [{}])[0].get("imageUrl")
    )

    if not image_url:
        # still nothing usable
        return jsonify(serialize_card(card)), 200

    # Save the image URL on the card
    card.image_url = image_url
    db.session.commit()

    return jsonify(serialize_card(card)), 200

