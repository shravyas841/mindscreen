from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_protected_route_rejects_missing_token():
    assert client.get("/api/auth/me").status_code == 401


def test_register_login_refresh_and_access_token_flow():
    email = "research-test@example.com"
    password = "correct-horse-battery"
    registered = client.post("/api/auth/register", json={
        "email": email, "password": password, "name": "Research Test", "has_consented": True
    })
    assert registered.status_code == 200, registered.text
    tokens = registered.json()

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == email

    refreshed = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    wrong_type = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert wrong_type.status_code == 401


def test_refresh_rejects_access_token():
    login = client.post(
        "/api/auth/login",
        json={"email": "research-test@example.com", "password": "correct-horse-battery"},
    )
    response = client.post("/api/auth/refresh", json={"refresh_token": login.json()["access_token"]})
    assert response.status_code == 401
