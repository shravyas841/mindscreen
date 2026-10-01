from fastapi.testclient import TestClient

from main import app
from routers import predict


client = TestClient(app)


def auth_headers(email: str) -> dict[str, str]:
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": "correct-horse-battery",
        "name": "API Test",
        "has_consented": True,
    })
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_fused_route_preserves_crisis_resource_and_missing_audio_flags(monkeypatch):
    headers = auth_headers("prediction-api@example.com")
    monkeypatch.setattr(predict, "get_fused_prediction", lambda *args, **kwargs: {
        "risk_level": "severe",
        "confidence": 0.9,
        "priority_score": 0.9,
        "probabilities": {"minimal": .7, "mild": .1, "moderate": .1, "severe": .1},
        "raw_probabilities": {"minimal": .7, "mild": .1, "moderate": .1, "severe": .1},
        "shap_data": {"words": []},
        "audio_features": None,
        "audio_present": False,
        "crisis_flag": False,
        "resource_display_flag": True,
        "phq_floor_applied": True,
        "text_inference_source": "keyword_fallback",
    })
    response = client.post("/api/predict/fused", headers=headers, json={
        "answers": [2, 2, 2, 2, 2, 2, 2, 1, 0],
        "text": "I have felt low for several days.",
        "audio_features": None,
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["crisis_flag"] is False
    assert body["resource_display_flag"] is True
    assert body["phq_floor_applied"] is True
    assert body["audio_present"] is False


def test_phq_endpoint_item9_is_r1_even_with_low_total():
    headers = auth_headers("phq-item9@example.com")
    response = client.post("/api/phq/submit", headers=headers, json={"answers": [0] * 8 + [1]})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["risk_level"] == "severe"
    assert body["crisis_flag"] is True
    assert body["resource_display_flag"] is True
    assert body["priority_score"] == 0.9


def test_phq_high_priority_without_item9_is_not_explicit_crisis():
    headers = auth_headers("phq-floor@example.com")
    response = client.post("/api/phq/submit", headers=headers, json={
        "answers": [3, 3, 3, 3, 1, 1, 1, 0, 0]
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["risk_level"] == "severe"
    assert body["crisis_flag"] is False
    assert body["resource_display_flag"] is True
