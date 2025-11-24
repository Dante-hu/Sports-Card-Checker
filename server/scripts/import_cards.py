import json
import os

from app import create_app
from app.extensions import db
from app.models.card import Card


def load_set(filepath):
    """Load one JSON file and return the list of cards."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def import_set(filepath):
    """Import all cards from one JSON file into the database."""
    data = load_set(filepath)

    created = 0
    skipped = 0

    for item in data:
        # Check if this card already exists (avoid duplicates)
        exists = Card.query.filter_by(
            sport=item["sport"],
            year=item["year"],
            brand=item["brand"],
            set_name=item["set_name"],
            card_number=item["card_number"],
        ).first()

        if exists:
            skipped += 1
            continue

        card = Card(
            sport=item["sport"],
            year=item["year"],
            brand=item["brand"],
            set_name=item["set_name"],
            card_number=item["card_number"],
            player_name=item["player_name"],
            team=item["team"],
            image_url=item["image_url"],
        )
        db.session.add(card)
        created += 1

    db.session.commit()
    print(f"{os.path.basename(filepath)} → Imported {created} cards, skipped {skipped} duplicates")


if __name__ == "__main__":
    # Create app + push app context so we can use the database
    app = create_app()
    with app.app_context():
        # Find the /data folder relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .. from /scripts
        data_dir = os.path.join(base_dir, "data")

        print(f"Looking for JSON files in: {data_dir}")

        # Loop over every .json file in /data and import it
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                full_path = os.path.join(data_dir, filename)
                print(f"Importing {full_path} ...")
                import_set(full_path)
