import pytest

# Uses the client fixture, not requests


@pytest.fixture
def sample_card_payload():
    return {
        "sport": "Hockey",
        "year": 2023,
        "brand": "Upper Deck",
        "set_name": "Series 1",
        "card_number": "201",
        "player_name": "Connor Bedard",
        "team": "Chicago Blackhawks",
        "image_url": None,
    }


def test_create_card_valid_payload(client, sample_card_payload):
    """POST /api/cards/ with full payload."""
    rsp = client.post("/api/cards", json=sample_card_payload)
    assert rsp.status_code == 201
    created = rsp.json
    for key, value in sample_card_payload.items():
        assert created[key] == value
    assert "id" in created  # DB assigned


def test_create_card_missing_field(client):
    """Return 400 if any required field is missing."""
    payload = {
        "sport": "Baseball",
        # missing required fields
    }
    rsp = client.post("/api/cards", json=payload)
    assert rsp.status_code == 400
    assert "Missing fields" in rsp.json["error"]


def test_list_cards_empty_db(client):
    """No cards → empty list."""
    rsp = client.get("/api/cards")
    assert rsp.status_code == 200
    assert rsp.json["items"] == []
    assert rsp.json["total"] == 0


def test_list_cards_with_sample(client):
    """Insert one card via POST, then list."""
    payload = {
        "sport": "Hockey",
        "year": 2023,
        "brand": "Upper Deck",
        "set_name": "Young Guns",
        "card_number": "201",
        "player_name": "Connor Bedard",
        "team": "Chicago Blackhawks",
    }
    create_rsp = client.post("/api/cards/", json=payload)
    assert create_rsp.status_code == 201

    rsp = client.get("/api/cards/")
    assert rsp.status_code == 200
    assert rsp.json["total"] == 1


def test_filter_by_sport(client):
    """Insert two sports, filter by one."""
    # Hockey card
    hockey_payload = {
        "sport": "Hockey",
        "year": 2023,
        "brand": "Upper Deck",
        "set_name": "Young Guns",
        "card_number": "201",
        "player_name": "Connor Bedard",
        "team": "Chicago Blackhawks",
    }
    r1 = client.post("/api/cards/", json=hockey_payload)
    assert r1.status_code == 201

    # Baseball card
    baseball_payload = {
        "sport": "Baseball",
        "year": 2022,
        "brand": "Topps",
        "set_name": "Series 1",
        "card_number": "100",
        "player_name": "Mike Trout",
        "team": "Angels",
    }
    r2 = client.post("/api/cards/", json=baseball_payload)
    assert r2.status_code == 201

    rsp = client.get("/api/cards/?sport=Hockey")
    assert rsp.status_code == 200
    assert rsp.json["total"] == 1


def test_pagination(client):
    """Create 25 cards, ask for page 2 (per_page=10)."""
    for i in range(25):
        client.post(
            "/api/cards",
            json={
                "sport": "Hockey",
                "year": 2020,
                "brand": "Test",
                "set_name": f"Set {i}",
                "card_number": str(i),
                "player_name": f"Player {i}",
                "team": "Team",
            },
        )
    rsp = client.get("/api/cards?page=2&per_page=10")
    assert rsp.status_code == 200
    assert len(rsp.json["items"]) == 10
    assert rsp.json["page"] == 2
    assert rsp.json["per_page"] == 10
    assert rsp.json["total"] == 25


def test_update_card(client, sample_card_payload):
    """PATCH /api/cards/<id> with new image URL."""
    # 1. create
    create_rsp = client.post("/api/cards", json=sample_card_payload)
    assert create_rsp.status_code == 201
    card_id = create_rsp.json["id"]

    # 2. update
    patch = {"image_url": "https://example.com/image.jpg"}
    rsp = client.patch(f"/api/cards/{card_id}", json=patch)
    assert rsp.status_code == 200
    assert rsp.json["image_url"] == "https://example.com/image.jpg"

    # 3. verify other fields unchanged
    assert rsp.json["player_name"] == sample_card_payload["player_name"]


def test_update_card_invalid_year(client):
    """Year must be integer."""
    payload = {
        "sport": "Hockey",
        "year": 2023,
        "brand": "Upper Deck",
        "set_name": "Young Guns",
        "card_number": "201",
        "player_name": "Connor Bedard",
        "team": "Chicago Blackhawks",
    }
    create_rsp = client.post("/api/cards/", json=payload)
    assert create_rsp.status_code == 201
    card_id = create_rsp.json["id"]

    rsp = client.patch(f"/api/cards/{card_id}", json={"year": "not-a-year"})
    assert rsp.status_code == 400


def test_get_card_by_id_404(client):
    """PATCH /api/cards/999999 → 404 (method allowed, id not found)."""
    rsp = client.patch("/api/cards/999999", json={"year": 2024})
    assert rsp.status_code == 404
