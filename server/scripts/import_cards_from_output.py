# server/scripts/import_cards_from_output.py

import os
import csv
from app import create_app
from app.extensions import db
from app.models.card import Card
from app.models.set import Set  # make sure this import path matches your project

# Folder where your scraper saves CSV files (relative to server/)
OUTPUT_FOLDER = "../scrapper/output"


def import_all_cards():
    app = create_app()

    with app.app_context():
        print(f"📂 Looking for CSV files in: {OUTPUT_FOLDER}")

        if not os.path.isdir(OUTPUT_FOLDER):
            print("❌ OUTPUT_FOLDER does not exist or is not a directory.")
            return

        total_added = 0

        # Track cards we've seen in THIS run to avoid dupes across CSVs
        seen_cards = set()

        # Track sets we already know exist (from DB or created earlier in this run)
        known_sets = set(
            (s.sport, s.year, s.brand, s.set_name) for s in Set.query.all()
        )

        # Loop over every CSV in scrapper/output
        for filename in os.listdir(OUTPUT_FOLDER):
            if not filename.lower().endswith(".csv"):
                continue

            csv_path = os.path.join(OUTPUT_FOLDER, filename)
            print(f"\n📥 Importing from: {csv_path}")

            new_sets_this_file = 0
            cards_to_add = []

            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    sport = row.get("sport")
                    year = row.get("year")
                    brand = row.get("brand")
                    set_name = row.get("set_name")
                    card_number = row.get("card_number")
                    player_name = row.get("player_name")
                    team = row.get("team")
                    image_url = row.get("image_url") or None
                    # we still read is_rookie but don't store it yet
                    # is_rookie_val = row.get("is_rookie")

                    # basic validation
                    if not card_number or not player_name or not set_name:
                        continue

                    # normalize card_number as *string* (DB column is varchar)
                    card_number_str = str(card_number).strip()
                    if card_number_str == "":
                        continue

                    # dedupe cards inside this import run (across ALL CSVs)
                    card_key = (sport, year, brand, set_name, card_number_str)
                    if card_key in seen_cards:
                        continue
                    seen_cards.add(card_key)

                    # 🔹 Ensure a Set exists for this combo
                    set_key = (sport, year, brand, set_name)
                    if set_key not in known_sets:
                        existing_set = Set.query.filter_by(
                            sport=sport,
                            year=year,
                            brand=brand,
                            set_name=set_name,
                        ).first()

                        if not existing_set:
                            new_set = Set(
                                sport=sport,
                                year=year,
                                brand=brand,
                                set_name=set_name,
                            )
                            db.session.add(new_set)
                            new_sets_this_file += 1

                        known_sets.add(set_key)

                    # dedupe against existing Card rows in DB
                    existing_card = Card.query.filter_by(
                        sport=sport,
                        year=year,
                        brand=brand,
                        set_name=set_name,
                        card_number=card_number_str,
                    ).first()

                    if existing_card:
                        continue

                    # Build Card (no is_rookie – your Card model doesn't have that field yet)
                    card = Card(
                        sport=sport,
                        year=year,
                        brand=brand,
                        set_name=set_name,
                        card_number=card_number_str,
                        player_name=player_name,
                        team=team,
                        image_url=image_url,
                    )
                    cards_to_add.append(card)

            # bulk insert cards for this file
            if cards_to_add:
                db.session.bulk_save_objects(cards_to_add)

            # commit if we added cards OR created sets
            if cards_to_add or new_sets_this_file:
                db.session.commit()

            if cards_to_add:
                print(f"✅ Added {len(cards_to_add)} cards from {filename}")
                total_added += len(cards_to_add)
            else:
                if new_sets_this_file:
                    print(
                        f"ℹ️ No new cards, but created {new_sets_this_file} sets from {filename}."
                    )
                else:
                    print(
                        f"ℹ️ No new cards or sets added from {filename} (all duplicates or invalid)."
                    )

        print(f"\n🎉 Done. Total new cards added from all CSVs: {total_added}")


if __name__ == "__main__":
    import_all_cards()
