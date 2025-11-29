# server/scripts/import_cards.py
import json
import os
from pathlib import Path

from app.extensions import db
from app.models.card import Card
from app.models.set import Set  # ✅ import Set


def load_set(filepath: Path):
    """Load one JSON file and return the list of cards."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def import_set(filepath: Path):
    """Import all cards from one JSON file into the database."""
    data = load_set(filepath)

    created = 0
    skipped = 0

    for item in data:
        sport = item["sport"]
        # store year consistently as string (handles 2024 and "2024-25")
        year = str(item["year"])
        brand = item["brand"]
        set_name = item["set_name"]

        # card_number may be int in JSON – force to string for Postgres
        card_number = str(item["card_number"])

        # ✅ make sure the Set exists (auto-create if needed)
        Set.get_or_create(
            sport=sport,
            year=year,
            brand=brand,
            set_name=set_name,
        )

        # Check if this card already exists (avoid duplicates)
        exists = Card.query.filter_by(
            sport=sport,
            year=year,
            brand=brand,
            set_name=set_name,
            card_number=card_number,
        ).first()

        if exists:
            skipped += 1
            continue

        card = Card(
            sport=sport,
            year=year,
            brand=brand,
            set_name=set_name,
            card_number=card_number,
            player_name=item["player_name"],
            team=item["team"],
            image_url=item["image_url"],
        )
        db.session.add(card)
        created += 1

    db.session.commit()
    print(
        f"{os.path.basename(filepath)} → Imported {created} cards, "
        f"skipped {skipped} duplicates"
    )


def seed_all_sets():
    """
    Look in the /data folder and import every .json file.
    Can be safely called multiple times because import_set skips duplicates.
    """
    # Find the /data folder relative to this file
    base_dir = Path(__file__).resolve().parents[1]  # go up from /scripts to /server
    data_dir = base_dir / "data"

    print(f"Looking for JSON files in: {data_dir}")

    if not data_dir.exists():
        print("⚠️  Data directory does not exist, skipping seeding.")
        return

    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            full_path = data_dir / filename
            print(f"Importing {full_path} ...")
            import_set(full_path)


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_all_sets()
