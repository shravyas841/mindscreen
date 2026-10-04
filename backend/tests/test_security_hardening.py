from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from jose import jwt

from config import settings
from database import SessionLocal
from main import app
from middleware.rate_limit import limiter
from models.assessment import Assessment
from models.user import User
from routers import chat, predict
from services.auth_service import create_access_token, create_refresh_token, hash_password


client = TestClient(app)


def _create_user_tokens() -> tuple[User, dict[str, str]]:
    db = SessionLocal()
    try:
        user = User(
            email=f"security-{uuid4()}@example.com",
            hashed_password=hash_password("correct-horse-battery"),
            name="Security Test",
            has_consented=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
    finally:
        db.close()
    return user, {
        "access": create_access_token({"sub": str(user_id)}),
        "refresh": create_refresh_token({"sub": str(user_id)}),
    }


def _authorization(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_invalid_access_and_expired_or_invalid_refresh_tokens_are_rejected():
    user, _ = _create_user_tokens()
    assert client.get("/api/auth/me", headers=_authorization("not-a-jwt")).status_code == 401

    expired = jwt.encode(
        {
            "sub": str(user.id),
            "type": "refresh",
            "jti": str(uuid4()),
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert client.post("/api/auth/refresh", json={"refresh_token": expired}).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": "not-a-jwt"}).status_code == 401


def test_expired_access_token_is_rejected():
    user, _ = _create_user_tokens()
    expired = jwt.encode(
        {
            "sub": str(user.id),
            "type": "access",
            "jti": str(uuid4()),
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    response = client.get("/api/auth/me", headers=_authorization(expired))
    assert response.status_code == 401


def test_wrong_token_types_are_rejected():
    _, tokens = _create_user_tokens()
    assert client.get(
        "/api/auth/me", headers=_authorization(tokens["refresh"])
    ).status_code == 401
    assert client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["access"]}
    ).status_code == 401


def test_refresh_rotation_replaces_and_invalidates_the_previous_refresh_token():
    _, tokens = _create_user_tokens()

    rotated = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh"]})
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["access_token"]
    assert rotated.json()["refresh_token"] != tokens["refresh"]

    reused = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh"]})
    assert reused.status_code == 401

    replacement = client.post(
        "/api/auth/refresh",
        json={"refresh_token": rotated.json()["refresh_token"]},
    )
    assert replacement.status_code == 200, replacement.text


def test_logout_revokes_refresh_token_and_is_idempotent_for_invalid_input():
    _, tokens = _create_user_tokens()

    logged_out = client.post("/api/auth/logout", json={"refresh_token": tokens["refresh"]})
    assert logged_out.status_code == 204
    assert client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh"]}
    ).status_code == 401
    assert client.post(
        "/api/auth/logout", json={"refresh_token": "already-invalid"}
    ).status_code == 204


def test_mood_data_is_owner_scoped_and_requires_authentication():
    _, user_a = _create_user_tokens()
    _, user_b = _create_user_tokens()
    headers_a = _authorization(user_a["access"])
    headers_b = _authorization(user_b["access"])

    created = client.post(
        "/api/mood/log",
        headers=headers_a,
        json={"mood_score": 2, "notes": "private mood note"},
    )
    assert created.status_code == 200, created.text
    record_id = created.json()["id"]

    history_a = client.get("/api/mood/trend", headers=headers_a)
    history_b = client.get("/api/mood/trend", headers=headers_b)
    anonymous = client.get("/api/mood/trend")

    assert history_a.status_code == 200
    assert any(record["id"] == record_id for record in history_a.json())
    assert history_b.status_code == 200
    assert all(record["id"] != record_id for record in history_b.json())
    assert anonymous.status_code == 401
    assert client.get(f"/api/mood/{record_id}", headers=headers_b).status_code == 404


def test_authenticated_rate_limits_are_stable_and_isolated_by_user():
    limiter.reset()
    _, user_a = _create_user_tokens()
    _, user_b = _create_user_tokens()
    payload = {"answers": [0] * 9}
    try:
        for _ in range(30):
            response = client.post(
                "/api/phq/submit",
                headers=_authorization(user_a["access"]),
                json=payload,
            )
            assert response.status_code == 200, response.text

        limited = client.post(
            "/api/phq/submit",
            headers=_authorization(user_a["access"]),
            json=payload,
        )
        assert limited.status_code == 429
        assert limited.json() == {"detail": "Rate limit exceeded"}

        other_user = client.post(
            "/api/phq/submit",
            headers=_authorization(user_b["access"]),
            json=payload,
        )
        assert other_user.status_code == 200, other_user.text
    finally:
        limiter.reset()


def test_provider_failure_logs_exclude_response_bodies_and_exception_messages(monkeypatch, caplog):
    secret_text = "private journal text and provider-secret-key"

    class FailedResponse:
        status_code = 500
        text = secret_text

    monkeypatch.setattr(chat.requests, "post", lambda *args, **kwargs: FailedResponse())
    with caplog.at_level("WARNING"):
        assert chat.call_gemini_llm("private message", [], "provider-secret-key") is None
        assert chat.call_hf_llm("private message", [], "provider-secret-key") is None
    assert secret_text not in caplog.text
    assert "provider-secret-key" not in caplog.text

    caplog.clear()
    monkeypatch.setattr(
        chat.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError(secret_text)),
    )
    with caplog.at_level("WARNING"):
        assert chat.call_gemini_llm("private message", [], "provider-secret-key") is None
    assert secret_text not in caplog.text
    assert "provider-secret-key" not in caplog.text


def test_fused_prediction_does_not_persist_raw_audio_or_journal_text(monkeypatch):
    user, tokens = _create_user_tokens()
    features = {
        "rms_mean": 0.2,
        "rms_std": 0.1,
        "zcr_mean": 0.3,
        "spectral_centroid": 0.4,
        "spectral_rolloff": 0.5,
        "speaking_ratio": 0.6,
    }
    monkeypatch.setattr(predict, "get_fused_prediction", lambda *args, **kwargs: {
        "risk_level": "minimal",
        "confidence": 0.8,
        "priority_score": 0.8,
        "probabilities": {"minimal": .8, "mild": .1, "moderate": .06, "severe": .04},
        "raw_probabilities": {"minimal": .8, "mild": .1, "moderate": .06, "severe": .04},
        "shap_data": {"words": []},
        "audio_features": features,
        "audio_present": True,
        "crisis_flag": False,
        "resource_display_flag": False,
        "phq_floor_applied": False,
        "text_inference_source": "test",
    })

    response = client.post(
        "/api/predict/fused",
        headers=_authorization(tokens["access"]),
        json={"answers": [0] * 9, "text": "private journal entry", "audio_features": features},
    )
    assert response.status_code == 200, response.text

    db = SessionLocal()
    try:
        stored = db.query(Assessment).filter(Assessment.user_id == user.id).one()
        assert stored.text_entry is None
        assert "audio_features" not in stored.__table__.columns
    finally:
        db.close()
