from types import SimpleNamespace

from fastapi.testclient import TestClient

from main import app
from routers import chat
from services.auth_service import get_current_user


client = TestClient(app)


def _post_companion(payload: dict):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    try:
        return client.post("/api/chat/companion", json=payload)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_crisis_input_is_blocked_before_provider_generation(monkeypatch):
    monkeypatch.setattr(chat.settings, "GEMINI_API_KEY", "test-key", raising=False)
    monkeypatch.setattr(chat.settings, "HF_TOKEN", "test-token", raising=False)
    monkeypatch.setattr(
        chat,
        "call_gemini_llm",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Gemini must not run")),
    )
    monkeypatch.setattr(
        chat,
        "call_hf_llm",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("HF must not run")),
    )

    response = _post_companion({"message": "I want to kill myself", "history": []})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["crisis_flag"] is True
    assert "Tele-MANAS" in body["helpline_info"]
    assert "iCall" in body["helpline_info"]
    assert not any(phrase in body["reply"].lower() for phrase in (
        "you are actually safe", "you are safe", "safe right now"
    ))


def test_non_crisis_input_returns_primary_provider_response(monkeypatch):
    monkeypatch.setattr(chat.settings, "GEMINI_API_KEY", "test-key", raising=False)
    monkeypatch.setattr(chat.settings, "HF_TOKEN", "test-token", raising=False)
    monkeypatch.setattr(chat, "call_gemini_llm", lambda *args, **kwargs: "A cautious primary-provider response.")
    monkeypatch.setattr(
        chat,
        "call_hf_llm",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("HF fallback must not run")),
    )

    response = _post_companion({"message": "I feel stressed about exams", "history": []})

    assert response.status_code == 200, response.text
    assert response.json()["reply"] == "A cautious primary-provider response."
    assert response.json()["crisis_flag"] is False


def test_non_crisis_input_preserves_provider_fallback_chain(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(chat.settings, "GEMINI_API_KEY", "test-key", raising=False)
    monkeypatch.setattr(chat.settings, "HF_TOKEN", "test-token", raising=False)
    monkeypatch.setattr(chat, "call_gemini_llm", lambda *args, **kwargs: calls.append("gemini") or None)
    monkeypatch.setattr(chat, "call_hf_llm", lambda *args, **kwargs: calls.append("hf") or "A cautious provider response.")

    response = _post_companion({"message": "I feel stressed about exams", "history": []})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["crisis_flag"] is False
    assert body["reply"] == "A cautious provider response."
    assert calls == ["gemini", "hf"]


def test_provider_failures_return_schema_valid_deterministic_template(monkeypatch):
    monkeypatch.setattr(chat.settings, "GEMINI_API_KEY", "test-key", raising=False)
    monkeypatch.setattr(chat.settings, "HF_TOKEN", "test-token", raising=False)
    monkeypatch.setattr(chat, "call_gemini_llm", lambda *args, **kwargs: None)
    monkeypatch.setattr(chat, "call_hf_llm", lambda *args, **kwargs: None)

    response = _post_companion({"message": "I feel stressed about exams", "history": []})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reply"] == chat.FALLBACK_RESPONSES["academic"][0]
    assert body["companion_name"] == "Saathi"
    assert body["crisis_flag"] is False
    assert body["helpline_info"] is None


def test_deterministic_responses_contain_no_unsupported_safety_assurance():
    forbidden = ("you are actually safe", "you are safe", "safe right now")
    responses = [reply for pool in chat.FALLBACK_RESPONSES.values() for reply in pool]
    assert all(not any(phrase in reply.lower() for phrase in forbidden) for reply in responses)
