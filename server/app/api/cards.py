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


@cards_bp.get("")
def list_cards():
    query = Card.query

    sport = request.args.get("sport")
    # year as raw string (no type=int), so it can match things like "2024-25"
    year = request.args.get("year")
    brand = request.args.get("brand")
    set_name = request.args.get("set")
    player = request.args.get("player")
    team = request.args.get("team")
    q = request.args.get("q")

    if sport:
        query = query.filter(Card.sport.ilike(f"%{sport}%"))

    if year:
        # use ilike so "2024" or "2024-25" both work
        like = f"%{year}%"
        query = query.filter(Card.year.ilike(like))

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
                Card.sport.ilike(like),
            )
        )

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=100, type=int)

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


# Keywords that usually mean multi-card images / sets / lots
BAD_TITLE_KEYWORDS = [
    "team set",
    "complete set",
    "factory set",
    "base set",
    "master set",
    "lot",
    "card lot",
    "mixed lot",
    "assorted",
    "random",
    "box",
    "case",
    "pick your card",
    "pick from list",
]


def looks_like_single_player_card(item: dict, card: Card) -> bool:
    """Heuristic filter to avoid team sets / lots / multi-player images."""
    title = (item.get("title") or "").lower()

    if not title:
        return False

    # Require the player's last name to be in the title, if we have one
    if card.player_name:
        parts = card.player_name.split()
        if parts:
            last_name = parts[-1].lower()
            if last_name not in title:
                return False

    # Reject anything that looks like a set / lot / box etc.
    for bad in BAD_TITLE_KEYWORDS:
        if bad in title:
            return False

    return True


@cards_bp.post("/<int:card_id>/auto-image")
def auto_fill_card_image(card_id: int):
    """
    Try to automatically fill card.image_url using a suitable eBay search result.

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
    # Ask for more than 1 so we can skip bad ones
    params = {
        "q": query,
        "limit": 10,
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

    chosen_url = None

    # Try to pick a "single player" card first
    for item in items:
        if not looks_like_single_player_card(item, card):
            continue

        image_url = item.get("image", {}).get("imageUrl") or (
            item.get("thumbnailImages") or [{}]
        )[0].get("imageUrl")
        if image_url:
            chosen_url = image_url
            break

    # If nothing passed the filter, fall back to the first image we can find
    if not chosen_url:
        for item in items:
            image_url = item.get("image", {}).get("imageUrl") or (
                item.get("thumbnailImages") or [{}]
            )[0].get("imageUrl")
            if image_url:
                chosen_url = image_url
                break

    if not chosen_url:
        # still nothing usable
        return jsonify(serialize_card(card)), 200

    # Save the image URL on the card
    card.image_url = chosen_url
    db.session.commit()

    return jsonify(serialize_card(card)), 200
