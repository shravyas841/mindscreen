from services.phq_service import calculate_phq_score
from services.ml_service import get_text_prediction
from services.audio_service import get_audio_prediction
from services.calibration_service import apply_temperature_scaling
from typing import Optional

DEFAULT_FUSION_WEIGHTS = {"text": 0.50, "audio": 0.30, "phq": 0.20}


def _validated_weights(weights: Optional[dict[str, float]]) -> dict[str, float]:
    selected = dict(DEFAULT_FUSION_WEIGHTS if weights is None else weights)
    if set(selected) != {"text", "audio", "phq"}:
        raise ValueError("Fusion weights must contain text, audio, and phq")
    if any(value < 0 for value in selected.values()):
        raise ValueError("Fusion weights cannot be negative")
    if abs(sum(selected.values()) - 1.0) > 1e-9:
        raise ValueError("Fusion weights must sum to 1.0")
    return selected


def get_fused_prediction(
    phq_answers: list[int],
    text: str,
    audio_features: Optional[dict] = None,
    audio_base64: Optional[str] = None,
    calibrate: bool = True,
    temperature: float = 1.20,
    weights: Optional[dict[str, float]] = None,
) -> dict:
    """
    Fuses predictions from three modality branches via weighted decision-level fusion,
    followed by a heuristic temperature score transformation and HRE overrides.

    Modality weights: Text 50% | Audio 30% | PHQ-9 20%
    Missing audio uses the documented prior [0.25, 0.45, 0.20, 0.10];
    it is not represented as an observed acoustic feature vector.
    After fusion, HRE (High-Risk Escalation) overrides apply:
      - PHQ-9 total score >= 20  → force severe, priority floor 0.90
      - PHQ-9 Item 9 > 0         → force severe, crisis flag
    """
    # 1. Text prediction (DistilRoBERTa via HuggingFace API with negation resolution)
    text_result = get_text_prediction(text)
    text_probs  = text_result["probabilities"]

    selected_weights = _validated_weights(weights)

    # 2. Audio prediction (descriptors when supplied; missing-audio prior otherwise)
    audio_result = get_audio_prediction(
        audio_base64=audio_base64,
        audio_features=audio_features,
    )
    audio_probs = audio_result["probabilities"]

    # 3. PHQ-9 rule-based score vector
    phq_result = calculate_phq_score(phq_answers)
    phq_probs  = phq_result.probabilities

    # 4. Weighted late fusion. Production defaults are T=0.50, A=0.30, Q=0.20.
    raw_fused = {
        label: (
            text_probs[label] * selected_weights["text"]
            + audio_probs[label] * selected_weights["audio"]
            + phq_probs[label] * selected_weights["phq"]
        )
        for label in ("minimal", "mild", "moderate", "severe")
    }

    # Defensive normalisation
    total = sum(raw_fused.values())
    normalized_probs = {k: v / total for k, v in raw_fused.items()}

    # 5. Heuristic temperature score transformation (not statistical calibration)
    if calibrate:
        final_probs = apply_temperature_scaling(normalized_probs, temperature=temperature)
    else:
        final_probs = {k: round(v, 4) for k, v in normalized_probs.items()}

    best_label = max(final_probs, key=final_probs.get)
    base_score = final_probs[best_label]
    priority_score = base_score

    # 6. High-Risk Escalation (HRE) Module
    total_score = sum(phq_answers)
    has_item9 = len(phq_answers) >= 9 and phq_answers[8] > 0
    
    # Check text crisis intent via negation service
    from services.negation_service import detect_crisis_intent
    text_crisis = detect_crisis_intent(text)["is_crisis"] if text else False

    explicit_crisis = has_item9 or text_crisis
    high_score = total_score >= 20

    # Rule 1: PHQ-9 total score >= 20
    if high_score:
        best_label = "severe"
        priority_score = max(0.90, priority_score)

    # Rule 2: Explicit-indicator escalation (Item 9 > 0 or crisis language)
    if explicit_crisis:
        best_label = "severe"
        priority_score = max(0.90, priority_score)

    # Resource display is shown for all tier-c3 assessments or explicit crises
    resource_display = explicit_crisis or (best_label == "severe")

    return {
        # The existing API key serializes internal c3 as "severe" for backward
        # compatibility; the UI presents this tier as "High Priority".
        "risk_level":            best_label,
        "priority_score":        priority_score,
        "base_score":            base_score,
        "probabilities":         final_probs,
        "raw_probabilities":     normalized_probs,
        "fusion_weights":        selected_weights,
        "crisis_flag":           explicit_crisis,
        "resource_display_flag": resource_display,
        "shap_data":             text_result["shap_data"],
        "audio_features":        audio_features,
        "audio_available":       audio_features is not None,
    }
