from services.phq_service import calculate_phq_score
from services.ml_service import get_text_prediction
from services.audio_service import get_audio_prediction
from services.calibration_service import apply_temperature_scaling
from typing import Optional

def get_fused_prediction(
    phq_answers: list[int],
    text: str,
    audio_features: Optional[dict] = None,
    audio_base64: Optional[str] = None,
    calibrate: bool = True,
    temperature: float = 1.20,
) -> dict:
    """
    Weighted decision-level fusion (text 0.50, audio 0.30, PHQ-9 0.20),
    renormalised over the modalities actually present, followed by a
    monotone temperature transform (T=1.2, not a calibration) and the
    safety layer:
      R0  PHQ-9 floor   final tier >= tier implied by the PHQ-9 total
      R1  Item 9 > 0    -> high-priority tier, crisis flag
      R2  crisis text   -> high-priority tier, crisis flag
    """
    # 1. Text prediction (emotion model via HF API, or keyword fallback)
    text_result = get_text_prediction(text)
    text_probs  = text_result["probabilities"]

    # 2. Audio prediction: only real browser-extracted features are used.
    #    The legacy base64 payload-size proxy is NOT an acoustic measurement
    #    and is no longer used; if no features are supplied the audio branch
    #    is treated as missing and the weights are renormalised (revision).
    audio_present = audio_features is not None
    audio_probs = get_audio_prediction(audio_features=audio_features)["probabilities"] if audio_present else None

    # 3. PHQ-9 rule-based score vector
    phq_result = calculate_phq_score(phq_answers)
    phq_probs  = phq_result.probabilities

    # 4. Weighted late fusion (w_T=0.50, w_A=0.30, w_Q=0.20), renormalised
    #    over the modalities that are actually present.
    weights = {"text": 0.50, "audio": 0.30 if audio_present else 0.0, "phq": 0.20}
    wsum = sum(weights.values())
    keys = ["minimal", "mild", "moderate", "severe"]
    raw_fused = {
        k: (weights["text"] * text_probs[k]
            + (weights["audio"] * audio_probs[k] if audio_present else 0.0)
            + weights["phq"] * phq_probs[k]) / wsum
        for k in keys
    }
    normalized_probs = raw_fused  # already on the simplex

    # 5. Temperature softening (monotone; does not change the arg-max)
    if calibrate:
        final_probs = apply_temperature_scaling(normalized_probs, temperature=temperature)
    else:
        final_probs = {k: round(v, 4) for k, v in normalized_probs.items()}

    best_label = max(final_probs, key=final_probs.get)
    base_score = final_probs[best_label]
    confidence = base_score

    # 6. Safety override layer (revision)
    #    R0  PHQ-9 floor:   final tier >= tier implied by the PHQ-9 total
    #                       (fusion may escalate but never de-escalate)
    #    R1  Item 9 > 0  -> high-priority tier + crisis flag
    #    R2  affirmative self-directed crisis language -> same as R1
    from services.negation_service import detect_crisis_intent
    order = {k: i for i, k in enumerate(keys)}
    phq_tier = phq_result.severity                      # minimal/mild/moderate/severe
    floor_applied = order[phq_tier] > order[best_label]
    if floor_applied:
        best_label = phq_tier
        confidence = max(0.90, confidence) if phq_tier == "severe" else confidence

    total_score = sum(phq_answers)
    has_item9 = len(phq_answers) >= 9 and phq_answers[8] > 0
    text_crisis = detect_crisis_intent(text)["is_crisis"] if text else False
    explicit_crisis = has_item9 or text_crisis
    if explicit_crisis:
        best_label = "severe"
        confidence = max(0.90, confidence)

    resource_display = explicit_crisis or (best_label == "severe")

    return {
        "risk_level":            best_label,
        "confidence":            confidence,
        "base_score":            base_score,
        "probabilities":         final_probs,
        "raw_probabilities":     normalized_probs,
        "crisis_flag":           explicit_crisis,
        "resource_display_flag": resource_display,
        "shap_data":             text_result["shap_data"],
        "audio_features":        audio_features,
        "audio_present":         audio_present,
        "phq_floor_applied":     floor_applied,
    }
