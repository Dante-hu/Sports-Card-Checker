import pytest


class TestOwnedCards:

    # ---------- helpers ----------
    def _signup(self, client):
        """Create test user and return cookie."""
        client.post(
            "/api/signup", json={"email": "test@example.com", "password": "secret"}
        )
        # login returns session cookie automatically
        client.post(
            "/api/login", json={"email": "test@example.com", "password": "secret"}
        )
        return client  # client now holds session

    def _sample_card(self, client):
        """Create a card via /api/cards/ and return its id."""
        payload = {
            "sport": "Hockey",
            "year": 2023,
            "brand": "Upper Deck",
            "set_name": "Young Guns",
            "card_number": "201",
            "player_name": "Connor Bedard",
            "team": "Chicago Blackhawks",
        }
        r = client.post("/api/cards/", json=payload)
        assert r.status_code == 201
        data = r.json
        assert "id" in data
        return data["id"]

    # ---------- tests ----------
    def test_list_empty(self, client):
        client = self._signup(client)
        r = client.get("/api/owned-cards")
        print("STATUS:", r.status_code, "LOCATION:", r.headers.get("Location"))
        assert r.status_code == 200
        assert r.json == []

    def test_add_owned_card(self, client):
        client = self._signup(client)
        card_id = self._sample_card(client)
        payload = {"card_id": card_id, "quantity": 3, "condition": "Mint"}
        r = client.post("/api/owned-cards", json=payload)
        assert r.status_code == 201
        data = r.json
        assert data["quantity"] == 3
        assert data["condition"] == "Mint"
        assert data["card"]["player_name"] == "Connor Bedard"
        assert data["card"]["image_url"] is None  # sample has no image

    def test_merge_quantities(self, client):
        client = self._signup(client)
        card_id = self._sample_card(client)
        client.post("/api/owned-cards", json={"card_id": card_id, "quantity": 2})
        r = client.post("/api/owned-cards", json={"card_id": card_id, "quantity": 5})
        assert r.status_code == 200
        assert r.json["quantity"] == 7  # 2 + 5

    def test_delete_one_copy(self, client):
        client = self._signup(client)
        card_id = self._sample_card(client)
        add = client.post("/api/owned-cards", json={"card_id": card_id, "quantity": 5})
        owned_id = add.json["id"]
        r = client.delete(f"/api/owned-cards/{owned_id}?count=1")
        assert r.status_code == 200
        assert r.json["remaining"] == 4

    def test_delete_last_copy(self, client):
        client = self._signup(client)
        card_id = self._sample_card(client)
        add = client.post("/api/owned-cards", json={"card_id": card_id, "quantity": 1})
        owned_id = add.json["id"]
        r = client.delete(f"/api/owned-cards/{owned_id}")
        assert r.status_code == 200
        assert r.json["deleted"] is True

    def test_list_after_add(self, client):
        client = self._signup(client)
        card_id = self._sample_card(client)
        client.post("/api/owned-cards", json={"card_id": card_id, "quantity": 1})
        r = client.get("/api/owned-cards")
        assert r.status_code == 200
        assert len(r.json) == 1
        assert r.json[0]["card"]["player_name"] == "Connor Bedard"

    def test_add_by_name(self, client):
        client = self._signup(client)
        # add the card first so it exists
        client.post(
            "/api/cards/",
            json={
                "sport": "Hockey",
                "year": 2023,
                "brand": "Upper Deck",
                "set_name": "Young Guns",
                "card_number": "201",
                "player_name": "Connor Bedard",
                "team": "Chicago Blackhawks",
            },
        )
        payload = {
            "player_name": "Connor Bedard",
            "year": 2023,
            "brand": "Upper Deck",
            "quantity": 2,
        }
        r = client.post("/api/owned-cards/by-name", json=payload)
        assert r.status_code == 201
        assert r.json["quantity"] == 2
        assert r.json["card"]["player_name"] == "Connor Bedard"

    def test_cannot_add_negative_qty(self, client):
        client = self._signup(client)
        card_id = self._sample_card(client)
        r = client.post("/api/owned-cards", json={"card_id": card_id, "quantity": -1})
        assert r.status_code == 400
        assert "positive" in r.json["error"]
