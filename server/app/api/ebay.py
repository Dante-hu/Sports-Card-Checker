# app/api/ebay.py
from flask import Blueprint, request, jsonify
from ..ebay_client import search_ebay_items

ebay_bp = Blueprint("ebay", __name__, url_prefix="/api/ebay")


@ebay_bp.get("/search")
def ebay_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing q parameter"}), 400

    try:
        data = search_ebay_items(q, limit=5)
        return jsonify(data)
    except Exception as e:
        # You can make this nicer later
        return jsonify({"error": str(e)}), 500
