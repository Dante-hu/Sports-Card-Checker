from flask import Blueprint, jsonify, request
from ..models.set import Set
from ..extensions import db
from ..models.card import Card

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


def serialize_set_with_total(s: Set) -> dict:
    """Base to_dict plus total number of cards in this set in the cards table."""
    data = s.to_dict()
    total_cards = (
        Card.query.filter_by(
            sport=s.sport,
            year=s.year,
            brand=s.brand,
            set_name=s.set_name,
        ).count()
    )
    data["total_cards"] = total_cards
    return data


@sets_bp.get("")
def list_sets():
    """
    Return ALL sets as a simple list (no server-side pagination).
    Frontend can filter client-side.
    """
    sets = (
        Set.query.order_by(
            Set.year.desc(),
            Set.brand,
            Set.set_name,
        )
        .all()
    )

    return jsonify([serialize_set_with_total(s) for s in sets])


@sets_bp.get("/<int:set_id>")
def get_set(set_id: int):
    s = Set.query.get(set_id)
    if not s:
        return jsonify({"error": f"Set with id {set_id} not found"}), 404

    return jsonify(serialize_set_with_total(s)), 200


@sets_bp.get("/<int:set_id>/cards")
def get_cards_for_set(set_id: int):
    """
    Return *all* cards for this set in a single response.

    We keep the same response shape as pagination (items, page, pages, etc.)
    but effectively there is only 1 page with all cards.
    """

    set_obj = Set.query.get(set_id)
    if not set_obj:
        return jsonify({"error": f"Set with id {set_id} not found"}), 404

    # Get ALL cards that belong to this set
    cards = (
        Card.query.filter_by(
            sport=set_obj.sport,
            year=set_obj.year,
            brand=set_obj.brand,
            set_name=set_obj.set_name,
        )
        .order_by(Card.card_number)
        .all()
    )

    items = [
        (
            c.to_dict()
            if hasattr(c, "to_dict")
            else {
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
        )
        for c in cards
    ]

    total = len(items)

    # Shape compatible with previous paginated version,
    # but now it's just 1 page with all cards.
    return jsonify(
        {
            "items": items,
            "page": 1,
            "per_page": total,
            "total": total,
            "pages": 1,
            "has_next": False,
            "has_prev": False,
        }
    )


@sets_bp.post("")
def create_set():
    """
    Create a set defined by sport + year + brand + set_name.
    Enforces uniqueness via database constraint AND code check.
    """
    data = request.get_json() or {}

    sport = data.get("sport")
    year = data.get("year")
    brand = data.get("brand")
    set_name = data.get("set_name")

    if not sport or year is None or not brand or not set_name:
        return (
            jsonify({"error": "sport, year, brand, and set_name are required"}),
            400,
        )

    # Check for existing set
    existing = Set.query.filter_by(
        sport=sport,
        year=year,
        brand=brand,
        set_name=set_name,
    ).first()

    if existing:
        return jsonify(serialize_set_with_total(existing)), 200

    new_set = Set(
        sport=sport,
        year=year,
        brand=brand,
        set_name=set_name,
    )

    db.session.add(new_set)
    db.session.commit()

    return jsonify(serialize_set_with_total(new_set)), 201
