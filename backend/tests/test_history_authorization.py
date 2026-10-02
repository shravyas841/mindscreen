from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _register(email: str) -> dict[str, str]:
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": "correct-horse-battery",
        "name": "History Test",
        "has_consented": True,
    })
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_history_is_scoped_to_authenticated_user_and_rejects_anonymous_access():
    user_a = _register("history-user-a@example.com")
    user_b = _register("history-user-b@example.com")

    created = client.post(
        "/api/phq/submit",
        headers=user_a,
        json={"answers": [1, 1, 0, 0, 1, 0, 0, 0, 0]},
    )
    assert created.status_code == 200, created.text

    history_a = client.get("/api/phq/history", headers=user_a)
    history_b = client.get("/api/phq/history", headers=user_b)
    anonymous = client.get("/api/phq/history")

    assert history_a.status_code == 200
    assert len(history_a.json()) == 1
    user_a_record_id = history_a.json()[0]["id"]
    assert history_a.json()[0]["phq_answers"] == [1, 1, 0, 0, 1, 0, 0, 0, 0]

    assert history_b.status_code == 200
    assert all(record["id"] != user_a_record_id for record in history_b.json())
    assert anonymous.status_code == 401

    # The current API exposes no assessment-by-ID route; an attempted lookup is unavailable.
    assert client.get(f"/api/phq/history/{user_a_record_id}", headers=user_b).status_code == 404
