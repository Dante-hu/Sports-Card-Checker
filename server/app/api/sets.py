from flask import Blueprint, jsonify, request
from ..models.set import Set
from ..extensions import db
from ..models.card import Card

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


@sets_bp.get("/")
def list_sets():
    # ?page=1&per_page=20
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    # safety cap so nobody asks for like 10,000 at once
    per_page = min(per_page, 100)

    pagination = Set.query.order_by(Set.year.desc(), Set.brand, Set.set_name).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return jsonify(
        {
            "items": [s.to_dict() for s in pagination.items],
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }
    )


@sets_bp.get("/<int:set_id>")
def get_set(set_id):
    s = Set.query.get(set_id)
    if not s:
        return jsonify({"error": f"Set with id {set_id} not found"}), 404

    return jsonify(s.to_dict()), 200


@sets_bp.get("/<int:set_id>/cards")
def get_cards_for_set(set_id):
    """
    Return cards belonging to a specific set, WITH pagination.
    We still match cards using the set's sport, year, brand, and set_name.
    """

    # pagination params: ?page=1&per_page=20
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    per_page = min(per_page, 100)  # safety cap

    # Find the set
    set_obj = Set.query.get(set_id)
    if not set_obj:
        return jsonify({"error": f"Set with id {set_id} not found"}), 404

    # Base query for cards in this set
    query = Card.query.filter_by(
        sport=set_obj.sport,
        year=set_obj.year,
        brand=set_obj.brand,
        set_name=set_obj.set_name,
    ).order_by(Card.card_number)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Serialize cards (use to_dict if it exists)
    items = [
        c.to_dict() if hasattr(c, "to_dict") else {
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
        for c in pagination.items
    ]

    return jsonify(
        {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }
    ), 200


@sets_bp.post("/")
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
        return jsonify({"error": "sport, year, brand, and set_name are required"}), 400

    # Check for existing set
    existing = Set.query.filter_by(
        sport=sport,
        year=year,
        brand=brand,
        set_name=set_name,
    ).first()

    if existing:
        return jsonify(existing.to_dict()), 200

    new_set = Set(
        sport=sport,
        year=year,
        brand=brand,
        set_name=set_name,
    )

    db.session.add(new_set)
    db.session.commit()

    return jsonify(new_set.to_dict()), 201
