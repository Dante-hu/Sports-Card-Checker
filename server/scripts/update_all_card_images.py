# server/scripts/update_all_card_images.py

import os
import time
import requests

from app import create_app
from app.extensions import db
from app.models.card import Card
from sqlalchemy import or_

# helper logic to filter out unwanted eBay results
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


def fetch_image_for_card(card: Card) -> str | None:
    """
    Call eBay API and return a chosen image URL for this card,
    or None if nothing suitable is found.
    """
    query = build_ebay_query_from_card(card)
    if not query:
        print(f"[SKIP] Card {card.id}: cannot build search query")
        return None

    token = os.environ.get("EBAY_OAUTH_TOKEN")
    marketplace = os.environ.get("EBAY_MARKETPLACE_ID", "EBAY_CA")

    if not token:
        print("EBAY_OAUTH_TOKEN is not set; cannot fetch images.")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace,
        "Content-Type": "application/json",
    }
    params = {
        "q": query,
        "limit": 10,  # fetch several results so we can filter
    }

    try:
        resp = requests.get(
            "https://api.ebay.com/buy/browse/v1/item_summary/search",
            headers=headers,
            params=params,
            timeout=10,
        )
    except requests.RequestException as exc:
        print(f"[ERROR] Card {card.id}: eBay request error: {exc}")
        return None

    if resp.status_code != 200:
        print(
            f"[ERROR] Card {card.id}: eBay non-200 {resp.status_code} "
            f"{resp.text[:200]!r}"
        )
        return None

    data = resp.json()
    items = data.get("itemSummaries") or []
    if not items:
        print(f"[INFO] Card {card.id}: no eBay items found for query {query!r}")
        return None

    # Try to pick a "single player" card first
    chosen_url = None

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

    return chosen_url


def update_all_card_images(only_missing: bool = True, sleep_seconds: float = 0.2):
    """
    Loop through cards and fill/refresh image_url using eBay.

    only_missing=True -> only update cards where image_url is NULL/empty.
    sleep_seconds -> pause between eBay calls to avoid hammering the API.
    """
    if not os.environ.get("EBAY_OAUTH_TOKEN"):
        print("ERROR: EBAY_OAUTH_TOKEN is not set. Aborting.")
        return

    query = Card.query

    if only_missing:
        query = query.filter(or_(Card.image_url.is_(None), Card.image_url == ""))

    cards = query.all()
    total = len(cards)
    print(f"Found {total} cards to process (only_missing={only_missing}).")

    processed = 0
    updated = 0

    for card in cards:
        processed += 1
        print(f"[{processed}/{total}] Card {card.id}: {card.player_name}")

        image_url = fetch_image_for_card(card)
        if image_url:
            card.image_url = image_url
            updated += 1
            print("  -> updated image_url")

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    db.session.commit()
    print(f"Done. Processed={processed}, updated={updated}.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        update_all_card_images(only_missing=True, sleep_seconds=0.2)
