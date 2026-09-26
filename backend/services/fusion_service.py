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

    # 2. Audio prediction (real features preferred; base64 fallback)
    audio_result = get_audio_prediction(
        audio_base64=audio_base64,
        audio_features=audio_features,
    )
    audio_probs = audio_result["probabilities"]

    # 3. PHQ-9 rule-based score vector
    phq_result = calculate_phq_score(phq_answers)
    phq_probs  = phq_result.probabilities

    # 4. Weighted late fusion  (w_T=0.50, w_A=0.30, w_Q=0.20)
    raw_fused = {
        "minimal":  text_probs["minimal"]  * 0.50 + audio_probs["minimal"]  * 0.30 + phq_probs["minimal"]  * 0.20,
        "mild":     text_probs["mild"]     * 0.50 + audio_probs["mild"]     * 0.30 + phq_probs["mild"]     * 0.20,
        "moderate": text_probs["moderate"] * 0.50 + audio_probs["moderate"] * 0.30 + phq_probs["moderate"] * 0.20,
        "severe":   text_probs["severe"]   * 0.50 + audio_probs["severe"]   * 0.30 + phq_probs["severe"]   * 0.20,
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
        "crisis_flag":           explicit_crisis,
        "resource_display_flag": resource_display,
        "shap_data":             text_result["shap_data"],
        "audio_features":        audio_features,
        "audio_available":       audio_features is not None,
    }
