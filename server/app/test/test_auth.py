import requests
from .settings import BASE_URL


def test_sign_up_and_login_flow(client):
    email = "selenium_test@example.com"
    password = "S3lenium!"

    # 1. sign up
    rsp = client.post("/api/signup", json={"email": email, "password": password})
    assert rsp.status_code == 201
    assert rsp.json["email"] == email

    # 2. log in
    rsp = client.post("/api/login", json={"email": email, "password": password})
    assert rsp.status_code == 200
    assert "Login successful" in rsp.json["message"]

    # 3. /me (session cookie automatically handled by test client)
    rsp = client.get("/api/me")
    assert rsp.status_code == 200
    assert rsp.json["email"] == email

    # 4. summary
    rsp = client.get("/api/me/summary")
    assert rsp.status_code == 200
    data = rsp.json
    assert data["owned"]["total_unique_cards"] == 0
