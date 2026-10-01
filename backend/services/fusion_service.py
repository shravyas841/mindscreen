"""Authoritative late-fusion and safety-policy implementation."""

from typing import Mapping, Optional

from services.audio_service import get_audio_prediction
from services.calibration_service import DEFAULT_TEMPERATURE, apply_temperature_scaling
from services.ml_service import get_text_prediction
from services.negation_service import detect_crisis_intent
from services.phq_service import calculate_phq_score


RISK_TIERS = ("minimal", "mild", "moderate", "severe")
DEPLOYED_WEIGHTS = {"text": 0.50, "audio": 0.30, "phq": 0.20}
SAFETY_SCORE_FLOOR = 0.90


def fuse_probabilities(
    text_probs: Mapping[str, float],
    phq_probs: Mapping[str, float],
    audio_probs: Optional[Mapping[str, float]] = None,
    *,
    weights: Mapping[str, float] = DEPLOYED_WEIGHTS,
) -> dict[str, float]:
    """Fuse tier-score vectors and renormalise over present modalities."""
    active = {"text": float(weights["text"]), "phq": float(weights["phq"])}
    if audio_probs is not None:
        active["audio"] = float(weights["audio"])
    if any(weight < 0 for weight in active.values()) or sum(active.values()) <= 0:
        raise ValueError("Fusion weights for present modalities must be non-negative and sum above zero")

    total_weight = sum(active.values())
    fused: dict[str, float] = {}
    for tier in RISK_TIERS:
        numerator = active["text"] * float(text_probs[tier])
        numerator += active["phq"] * float(phq_probs[tier])
        if audio_probs is not None:
            numerator += active["audio"] * float(audio_probs[tier])
        fused[tier] = numerator / total_weight
    return fused


def apply_safety_rules(
    fused_tier: str,
    phq_tier: str,
    item9_positive: bool,
    text_crisis: bool,
    base_score: float,
) -> dict:
    """Apply R0 (PHQ floor), R1 (Item 9), and R2 (crisis language)."""
    order = {tier: index for index, tier in enumerate(RISK_TIERS)}
    if fused_tier not in order or phq_tier not in order:
        raise ValueError("Unknown risk tier")

    floor_applied = order[phq_tier] > order[fused_tier]
    final_tier = phq_tier if floor_applied else fused_tier
    explicit_crisis = bool(item9_positive or text_crisis)
    if explicit_crisis:
        final_tier = "severe"

    priority_score = float(base_score)
    if final_tier == "severe" and (floor_applied or explicit_crisis):
        priority_score = max(SAFETY_SCORE_FLOOR, priority_score)

    return {
        "risk_level": final_tier,
        "priority_score": priority_score,
        "crisis_flag": explicit_crisis,
        "resource_display_flag": explicit_crisis or final_tier == "severe",
        "phq_floor_applied": floor_applied,
    }


def get_fused_prediction(
    phq_answers: list[int],
    text: str,
    audio_features: Optional[dict] = None,
    *,
    calibrate: bool = True,
    temperature: float = DEFAULT_TEMPERATURE,
) -> dict:
    """Run deployed 0.50/0.30/0.20 fusion followed by R0, R1, and R2."""
    text_result = get_text_prediction(text)
    phq_result = calculate_phq_score(phq_answers)
    audio_present = audio_features is not None
    audio_result = get_audio_prediction(audio_features=audio_features) if audio_present else None

    raw_fused = fuse_probabilities(
        text_result["probabilities"],
        phq_result.probabilities,
        audio_result["probabilities"] if audio_result else None,
    )
    tier_scores = (
        apply_temperature_scaling(raw_fused, temperature=temperature)
        if calibrate
        else {tier: round(score, 4) for tier, score in raw_fused.items()}
    )
    fused_tier = max(tier_scores, key=tier_scores.get)
    base_score = tier_scores[fused_tier]
    crisis_result = detect_crisis_intent(text) if text else {"is_crisis": False}
    safety = apply_safety_rules(
        fused_tier=fused_tier,
        phq_tier=phq_result.severity,
        item9_positive=phq_answers[8] > 0,
        text_crisis=bool(crisis_result["is_crisis"]),
        base_score=base_score,
    )

    return {
        **safety,
        # Kept for existing clients; priority_score is the precise name.
        "confidence": safety["priority_score"],
        "base_score": base_score,
        "probabilities": tier_scores,
        "raw_probabilities": raw_fused,
        "shap_data": text_result["shap_data"],
        "audio_features": audio_features,
        "audio_present": audio_present,
        "crisis_trigger": crisis_result.get("trigger"),
        "text_inference_source": text_result.get("inference_source", "unknown"),
    }
