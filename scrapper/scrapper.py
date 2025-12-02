import re
import os
import pandas as pd
from bs4 import BeautifulSoup

HTML_FOLDER = "scrapehtml"
OUTPUT_FOLDER = "output"
OUTPUT_CSV = "all_cards.csv"


def extract_metadata(soup: BeautifulSoup):
    """
    Pull sport, year, brand, set_name from breadcrumbs / hidden field.
    Designed for SportsCardChecklist-style pages.
    """
    # SPORT (from hidden input if present, fallback to Hockey)
    sport = "Hockey"
    sport_input = soup.find("input", {"name": "sport"})
    if sport_input and sport_input.get("value"):
        sport = sport_input["value"].strip()

    year = None
    brand = None
    set_name = None

    # Breadcrumbs e.g. ["Hockey Checklists", "2024-25 Checklists",
    #                  "2024-25 O-Pee-Chee", "Base Hockey Cards"]
    crumb_spans = soup.select("ol.breadcrumb span[itemprop='name']")
    crumb_texts = [span.get_text(strip=True) for span in crumb_spans]

    # YEAR: first "2024-25" style thing
    for text in crumb_texts:
        m = re.search(r"\d{4}-\d{2}", text)
        if m:
            year = m.group(0)
            break

    # Fallback: plain 4-digit year like "2025" (e.g. "2025 Checklists", "2025 Topps")
    if not year:
        for text in crumb_texts:
            m = re.search(r"\b(19|20)\d{2}\b", text)
            if m:
                year = m.group(0)
                break

    # BRAND: from e.g. "2024-25 O-Pee-Chee" or "2025 Topps" → strip year
    if year:
        for text in crumb_texts:
            if year in text and "Checklists" not in text:
                brand = text.replace(year, "").strip(" -")
                break

    # SET NAME: last breadcrumb, cleaned
    if crumb_texts:
        raw = crumb_texts[-1]  # e.g. "Base Hockey Cards" or "Base Cards"
        cleaned = re.sub(
            r"\b(Cards?|Card|Hockey|Baseball|Checklist|Checklists|"
            r"Trading Card Checklists and Product Information)\b",
            "",
            raw,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
        set_name = cleaned or raw

    return (
        sport or "",
        year or "",
        brand or "",
        set_name or "",
    )


def clean_player_name(raw: str) -> str:
    """
    'Macklin Celebrini/Will Smith Young Gun' -> 'Macklin Celebrini/Will Smith'
    (keeps multiple names, just strips 'Young Gun(s)')
    """
    if raw is None:
        return ""
    # Remove Young Guns text
    cleaned = re.sub(r"\bYoung Guns?\b", "", raw, flags=re.IGNORECASE).strip()
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def normalize_name_for_key(name: str) -> str:
    """
    Normalize player names for key comparison, so:
      "Drew O'Connor" and "Drew O\\'Connor" are treated the same.
    """
    if not name:
        return ""
    # Turn escaped apostrophes into real ones
    name = name.replace("\\'", "'")
    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name


def parse_scc_file(path: str):
    """
    Parse a single HTML file and return a list of card dicts.
    De-duplicates within this file using a key.
    """
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    sport, year, brand, set_name = extract_metadata(soup)
    print(
        f"  → Metadata: sport='{sport}', year='{year}', "
        f"brand='{brand}', set_name='{set_name}'"
    )

    # key: (sport, year, brand, set_name, card_number, player_name)
    cards_by_key: dict[tuple, dict] = {}

    def upsert_card(card: dict):
        # Normalize the player name *inside* the stored card
        card["player_name"] = normalize_name_for_key(card.get("player_name", ""))
        key = (
            card["sport"],
            card["year"],
            card["brand"],
            card["set_name"],
            str(card["card_number"]),
            card["player_name"],
        )
        existing = cards_by_key.get(key)
        if existing is None:
            cards_by_key[key] = card
        else:
            # Prefer image_url if the new card has one
            if not existing.get("image_url") and card.get("image_url"):
                existing["image_url"] = card["image_url"]
            # Prefer team if missing before
            if not existing.get("team") and card.get("team"):
                existing["team"] = card["team"]
            # If either version says it's a rookie, mark as rookie
            if card.get("is_rookie"):
                existing["is_rookie"] = True

    # -------------------------------------------------
    # 1) Original "panel" layout (e.g., Young Guns)
    # -------------------------------------------------
    for panel in soup.select("div.panel.panel-primary"):
        h5 = panel.find("h5")
        if not h5:
            continue

        header_text = h5.get_text(" ", strip=True)

        # "2024-25 Upper Deck  #499 Macklin Celebrini/Will Smith Young Gun"
        m = re.search(r"#(\d+)\s+(.*)", header_text)
        if not m:
            continue

        card_number_str = m.group(1)
        player_raw = m.group(2).strip()

        try:
            card_number = int(card_number_str)
        except ValueError:
            card_number = card_number_str

        player_name = clean_player_name(player_raw)

        # TEAM
        team_div = panel.select_one("div.border-muted.border-bottom")
        team = None
        if team_div:
            for small in team_div.find_all("small"):
                small.extract()
            team_text = team_div.get_text(" ", strip=True)
            team = team_text or None

        # ROOKIE?
        rc_badge = panel.find("div", class_=re.compile(r"badge.*danger"))
        is_rookie = False
        if rc_badge and "RC" in rc_badge.get_text(strip=True).upper():
            is_rookie = True

        upsert_card(
            {
                "sport": sport,
                "year": year,
                "brand": brand,
                "set_name": set_name,
                "card_number": card_number,
                "player_name": player_name,
                "team": team,
                "image_url": None,  # may be filled later by gallery
                "is_rookie": is_rookie,
            }
        )

    # -------------------------------------------------
    # 2) New OPC / gallery layout with images
    #    (only front thumbnail image, e.g. front_thumb_16218044.jpg)
    # -------------------------------------------------
    for row in soup.select("div.row.border-separator"):
        gallery = row.select_one("div.gallery-wrapper")
        if not gallery:
            continue

        # Find the *front* image only (keep thumbnail!)
        front_img_url = None
        for a in gallery.select("a.popup-image"):
            href = a.get("href") or ""
            img = a.find("img")
            src = img.get("src") if img else ""

            if "front_" in href or "front_thumb_" in src:
                # ✅ keep thumbnail if that's what the HTML gives
                front_img_url = src or href
                break

        if not front_img_url:
            continue

        # The number + player name lives in the hidden "ebay_search" input
        # e.g. value="2024-25 O-Pee-Chee  23 Rasmus Dahlin "
        search_input = row.select_one("input[name='ebay_search']")
        if not search_input:
            continue

        value = search_input.get("value", "").strip()
        m = re.search(r"\s+(\d+)\s+(.+?)\s*$", value)
        if not m:
            continue

        card_number_str = m.group(1)
        player_raw = m.group(2).strip()

        try:
            card_number = int(card_number_str)
        except ValueError:
            card_number = card_number_str

        player_name = clean_player_name(player_raw)

        upsert_card(
            {
                "sport": sport,
                "year": year,
                "brand": brand,
                "set_name": set_name,
                "card_number": card_number,
                "player_name": player_name,
                "team": None,               # no team in this layout
                "image_url": front_img_url,  # ✅ thumbnail URL from page
                "is_rookie": False,
            }
        )

    # Return one row per unique card (for this single file)
    return list(cards_by_key.values())


def dedupe_global(cards: list[dict]) -> list[dict]:
    """
    Final global de-duplication across ALL files.

    Key: (sport, year, brand, set_name, card_number, player_name)

    If duplicates found:
      - keep one
      - fill in image_url/team/is_rookie with best available data.
    """
    by_key: dict[tuple, dict] = {}

    for card in cards:
        # Normalize player name for the global key too
        name = normalize_name_for_key(card.get("player_name", ""))
        card["player_name"] = name

        key = (
            card.get("sport", ""),
            card.get("year", ""),
            card.get("brand", ""),
            card.get("set_name", ""),
            str(card.get("card_number", "")),
            name,
        )
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = card
        else:
            # Prefer image_url if new one has it
            if not existing.get("image_url") and card.get("image_url"):
                existing["image_url"] = card["image_url"]
            # Prefer team if existing is missing it
            if not existing.get("team") and card.get("team"):
                existing["team"] = card["team"]
            # Merge rookie flag
            if card.get("is_rookie"):
                existing["is_rookie"] = True

    return list(by_key.values())


def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    all_cards = []

    for filename in os.listdir(HTML_FOLDER):
        if not filename.lower().endswith(".html"):
            continue

        html_path = os.path.join(HTML_FOLDER, filename)
        print(f"\nScraping file: {html_path}")
        cards = parse_scc_file(html_path)
        print(f"  → Extracted {len(cards)} cards (after per-file de-dup)")
        all_cards.extend(cards)

    print(f"\nTOTAL raw cards from all files (before global de-dup): {len(all_cards)}")

    # 🔥 Final global de-duplication
    unique_cards = dedupe_global(all_cards)
    print(f"TOTAL unique cards after global de-dup: {len(unique_cards)}")

    df = pd.DataFrame(unique_cards)
    out_path = os.path.join(OUTPUT_FOLDER, OUTPUT_CSV)
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Saved combined CSV to: {out_path}")


if __name__ == "__main__":
    main()
