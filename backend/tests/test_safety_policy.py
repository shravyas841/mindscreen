import pytest

from services import fusion_service
from services.fusion_service import apply_safety_rules, fuse_probabilities
from services.phq_service import calculate_phq_score
from services.audio_service import get_audio_prediction


TIERS = ["minimal", "mild", "moderate", "severe"]


@pytest.mark.parametrize(
    ("total", "expected"),
    [(0, "minimal"), (4, "minimal"), (5, "mild"), (9, "mild"),
     (10, "moderate"), (14, "moderate"), (15, "severe"), (27, "severe")],
)
def test_phq_band_boundaries(total, expected):
    answers = [0] * 9
    for index in range(9):
        take = min(3, total)
        answers[index] = take
        total -= take
    assert calculate_phq_score(answers).severity == expected


def test_minimal_phq_vector_matches_paper():
    assert calculate_phq_score([0] * 9).probabilities == {
        "minimal": 0.80, "mild": 0.15, "moderate": 0.04, "severe": 0.01
    }


def test_fusion_uses_deployed_weights_when_audio_present():
    text = dict(zip(TIERS, [1.0, 0.0, 0.0, 0.0]))
    audio = dict(zip(TIERS, [0.0, 1.0, 0.0, 0.0]))
    phq = dict(zip(TIERS, [0.0, 0.0, 1.0, 0.0]))
    assert fuse_probabilities(text, phq, audio) == {
        "minimal": 0.5, "mild": 0.3, "moderate": 0.2, "severe": 0.0
    }


def test_missing_audio_renormalises_over_text_and_phq():
    text = dict(zip(TIERS, [1.0, 0.0, 0.0, 0.0]))
    phq = dict(zip(TIERS, [0.0, 0.0, 1.0, 0.0]))
    result = fuse_probabilities(text, phq)
    assert result["minimal"] == pytest.approx(0.5 / 0.7)
    assert result["moderate"] == pytest.approx(0.2 / 0.7)
    assert sum(result.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(("fused", "phq", "expected"), [
    ("minimal", "mild", "mild"),
    ("mild", "moderate", "moderate"),
    ("minimal", "severe", "severe"),
    ("severe", "mild", "severe"),
])
def test_r0_never_allows_a_tier_below_phq(fused, phq, expected):
    result = apply_safety_rules(fused, phq, False, False, 0.4)
    assert result["risk_level"] == expected
    assert result["crisis_flag"] is False


def test_r1_item9_sets_explicit_crisis_and_score_floor():
    result = apply_safety_rules("minimal", "minimal", True, False, 0.3)
    assert result == {
        "risk_level": "severe",
        "priority_score": 0.9,
        "crisis_flag": True,
        "resource_display_flag": True,
        "phq_floor_applied": False,
    }


def test_r2_affirmative_text_sets_explicit_crisis():
    result = apply_safety_rules("mild", "mild", False, True, 0.5)
    assert result["risk_level"] == "severe"
    assert result["crisis_flag"] is True
    assert result["priority_score"] == 0.9


def test_high_priority_without_explicit_crisis_still_displays_resources():
    result = apply_safety_rules("severe", "severe", False, False, 0.7)
    assert result["crisis_flag"] is False
    assert result["resource_display_flag"] is True
    assert result["priority_score"] == 0.7


def test_fused_prediction_reports_missing_audio_and_r0(monkeypatch):
    monkeypatch.setattr(fusion_service, "get_text_prediction", lambda text: {
        "probabilities": {"minimal": .9, "mild": .05, "moderate": .03, "severe": .02},
        "shap_data": {"words": []},
    })
    result = fusion_service.get_fused_prediction([2, 2, 2, 2, 2, 2, 2, 1, 0], "I feel okay")
    assert result["risk_level"] == "severe"
    assert result["phq_floor_applied"] is True
    assert result["audio_present"] is False
    assert result["crisis_flag"] is False
    assert result["resource_display_flag"] is True


def test_audio_score_requires_real_feature_input():
    with pytest.raises(ValueError):
        get_audio_prediction(None)
