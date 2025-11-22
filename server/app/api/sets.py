from flask import Blueprint, jsonify
from ..models.set import Set

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


@sets_bp.get("/")
def list_sets():
    sets = Set.query.all()
    return jsonify([
        {
            "id": s.id,
            "sport": s.sport,
            "year": s.year,
            "brand": s.brand,
            "set_name": s.set_name,
        }
        for s in sets
    ])
