import asyncio
from types import SimpleNamespace

import pytest

from routers import phq as phq_router
from routers import predict as predict_router
from schemas.assessment import PHQSubmitRequest, PredictTextRequest
from services import fusion_service
from services.audio_service import get_audio_prediction
from services.negation_service import detect_crisis_intent


def _neutral_text_prediction(_text: str) -> dict:
    return {
        "risk_level": "minimal",
        "confidence": 0.70,
        "probabilities": {
            "minimal": 0.70,
            "mild": 0.15,
            "moderate": 0.10,
            "severe": 0.05,
        },
        "shap_data": {"words": []},
    }


class _FakeSession:
    def add(self, _value):
        pass

    def commit(self):
        pass

    def refresh(self, _value):
        pass


@pytest.fixture(autouse=True)
def deterministic_text_branch(monkeypatch):
    monkeypatch.setattr(fusion_service, "get_text_prediction", _neutral_text_prediction)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("I want to die.", True),
        ("I want to end my life.", True),
        ("I don't want to be alive anymore.", True),
        ("I no longer want to live.", True),
        ("I plan to overdose.", True),
        ("I was killing it at work, but now I want to die.", True),
        ("My friend abandoned me and now I want to die.", True),
        ("I am not okay and I want to die.", True),
        ("I don't want to die.", False),
        ("I do not want to kill myself.", False),
        ("My friend said they want to die.", False),
        ("She told me she wants to kill herself.", False),
        ('My friend said "I want to die."', False),
        ("I was killing it at work today.", False),
        ("That exam killed me.", False),
    ],
)
def test_crisis_language_scope(text, expected):
    assert detect_crisis_intent(text)["is_crisis"] is expected


def test_hre_high_score_is_not_acute_crisis():
    result = fusion_service.get_fused_prediction(
        [3, 3, 3, 3, 2, 2, 2, 2, 0], "I am completing the questionnaire."
    )
    assert result["risk_level"] == "severe"
    assert result["priority_score"] >= 0.90
    assert result["crisis_flag"] is False
    assert result["resource_display_flag"] is True


def test_hre_item9_sets_crisis_and_resources():
    result = fusion_service.get_fused_prediction(
        [0, 0, 0, 0, 0, 0, 0, 0, 1], "I am completing the questionnaire."
    )
    assert result["risk_level"] == "severe"
    assert result["priority_score"] >= 0.90
    assert result["crisis_flag"] is True
    assert result["resource_display_flag"] is True


def test_hre_affirmative_text_sets_crisis_and_resources():
    result = fusion_service.get_fused_prediction([0] * 9, "I want to die.")
    assert result["risk_level"] == "severe"
    assert result["priority_score"] >= 0.90
    assert result["crisis_flag"] is True
    assert result["resource_display_flag"] is True


def test_ordinary_case_has_no_hre_flags():
    result = fusion_service.get_fused_prediction([0] * 9, "I had an ordinary day.")
    assert result["risk_level"] == "minimal"
    assert result["priority_score"] < 0.90
    assert result["crisis_flag"] is False
    assert result["resource_display_flag"] is False


def test_missing_audio_is_explicit():
    result = fusion_service.get_fused_prediction([0] * 9, "I had an ordinary day.")
    assert result["audio_available"] is False
    assert result["audio_features"] is None
    assert get_audio_prediction()["probabilities"] == {
        "minimal": 0.25,
        "mild": 0.45,
        "moderate": 0.20,
        "severe": 0.10,
    }


def test_supplied_audio_is_explicit():
    features = {
        "rms_mean": 0.30,
        "rms_std": 0.10,
        "zcr_mean": 0.30,
        "spectral_centroid": 0.40,
        "spectral_rolloff": 0.40,
        "speaking_ratio": 0.50,
    }
    result = fusion_service.get_fused_prediction(
        [0] * 9, "I had an ordinary day.", audio_features=features
    )
    assert result["audio_available"] is True
    assert result["audio_features"] == features


def test_raw_audio_without_descriptors_uses_missing_audio_policy():
    result = fusion_service.get_fused_prediction(
        [0] * 9,
        "I had an ordinary day.",
        audio_base64="data:audio/webm;base64,YXVkaW8=",
    )
    assert result["audio_available"] is False
    assert result["audio_features"] is None
    assert get_audio_prediction(audio_base64="YXVkaW8=")["probabilities"] == {
        "minimal": 0.25,
        "mild": 0.45,
        "moderate": 0.20,
        "severe": 0.10,
    }


def test_phq_endpoint_item9_forces_high_priority_tier():
    response = asyncio.run(phq_router.submit_phq(
        PHQSubmitRequest(answers=[0, 0, 0, 0, 0, 0, 0, 0, 1]),
        db=_FakeSession(),
        current_user=SimpleNamespace(id=1),
    ))
    assert response.risk_level == "severe"
    assert response.priority_score >= 0.90
    assert response.crisis_flag is True
    assert response.resource_display_flag is True


def test_text_endpoint_affirmative_crisis_applies_hre(monkeypatch):
    monkeypatch.setattr(predict_router, "get_text_prediction", _neutral_text_prediction)
    response = asyncio.run(predict_router.predict_text(
        PredictTextRequest(text="I want to die."),
        db=_FakeSession(),
        current_user=SimpleNamespace(id=1),
    ))
    assert response.risk_level == "severe"
    assert response.priority_score >= 0.90
    assert response.crisis_flag is True
    assert response.resource_display_flag is True
