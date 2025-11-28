import pytest


class TestSets:

    # ---------- helpers ----------
    def _sample_set(self, client):
        """Create a set via API and return id."""
        payload = {
            "sport": "Hockey",
            "year": 2023,
            "brand": "Upper Deck",
            "set_name": "Series 1",
        }
        r = client.post("/api/sets", json=payload)
        assert r.status_code == 201
        return r.json["id"]

    # ---------- tests ----------
    def test_list_sets_empty(self, client):
        """No sets → empty list."""
        r = client.get("/api/sets")
        assert r.status_code == 200
        assert r.json["items"] == []
        assert r.json["total"] == 0

    def test_create_set(self, client):
        """POST /api/sets creates row."""
        payload = {
            "sport": "Basketball",
            "year": 2022,
            "brand": "Panini",
            "set_name": "Prizm",
        }
        r = client.post("/api/sets", json=payload)
        assert r.status_code == 201
        data = r.json
        assert data["sport"] == "Basketball"
        assert data["year"] == 2022
        assert data["brand"] == "Panini"
        assert data["set_name"] == "Prizm"

    def test_create_set_duplicate(self, client):
        """Duplicate (sport,year,brand,set) returns 200 + existing row."""
        payload = {
            "sport": "Baseball",
            "year": 2021,
            "brand": "Topps",
            "set_name": "Series 1",
        }
        first = client.post("/api/sets", json=payload)
        assert first.status_code == 201
        second = client.post("/api/sets", json=payload)
        assert second.status_code == 200
        assert second.json["id"] == first.json["id"]

    def test_get_set_by_id(self, client):
        set_id = self._sample_set(client)
        r = client.get(f"/api/sets/{set_id}")
        assert r.status_code == 200
        assert r.json["sport"] == "Hockey"

    def test_get_set_404(self, client):
        r = client.get("/api/sets/999999")
        assert r.status_code == 404
        assert "not found" in r.json["error"]

    def test_list_sets_pagination(self, client):
        # create 25 sets
        for i in range(25):
            client.post(
                "/api/sets",
                json={
                    "sport": "Football",
                    "year": 2020,
                    "brand": "Test",
                    "set_name": f"Set {i}",
                },
            )
        # ask for page 2, per_page 10
        r = client.get("/api/sets?page=2&per_page=10")
        assert r.status_code == 200
        assert len(r.json["items"]) == 10
        assert r.json["page"] == 2
        assert r.json["per_page"] == 10
        assert r.json["total"] == 25

    def test_create_set_missing_field(self, client):
        payload = {"sport": "Soccer"}  # missing year, brand, set_name
        r = client.post("/api/sets", json=payload)
        assert r.status_code == 400
        assert "required" in r.json["error"]

    def test_get_cards_for_set(self, client):
        set_id = self._sample_set(client)
        # ---- debug ----
        s = client.get(f"/api/sets/{set_id}").json
        print("SET:", s)
        # create cards and **check each response**
        for i in range(5):
            r = client.post(
                "/api/cards",
                json={
                    "sport": s["sport"],
                    "year": s["year"],
                    "brand": s["brand"],
                    "set_name": s["set_name"],
                    "card_number": str(i),
                    "player_name": f"Player {i}",
                    "team": "Team",
                },
            )
            print("CARD CREATE:", r.status_code, r.json)
            assert r.status_code == 201  # ← fail fast if card creation fails
        # ---- end debug ----
        r = client.get(f"/api/sets/{set_id}/cards")
        assert r.status_code == 200
        assert len(r.json["items"]) == 5

    def test_cards_for_set_pagination(self, client):
        set_id = self._sample_set(client)
        # create 30 cards
        for i in range(30):
            client.post(
                "/api/cards",
                json={
                    "sport": "Hockey",
                    "year": 2023,
                    "brand": "Upper Deck",
                    "set_name": "Series 1",
                    "card_number": str(i),
                    "player_name": f"Player {i}",
                    "team": "Team",
                },
            )
        # page 2, per_page 10
        r = client.get(f"/api/sets/{set_id}/cards?page=2&per_page=10")
        assert r.status_code == 200
        assert len(r.json["items"]) == 10
        assert r.json["page"] == 2
        assert r.json["per_page"] == 10
        assert r.json["total"] == 30

    def test_per_page_cap(self, client):
        # ask for 500 – should be capped at 100
        r = client.get("/api/sets?per_page=500")
        assert r.status_code == 200
        assert r.json["per_page"] == 100  # capped
