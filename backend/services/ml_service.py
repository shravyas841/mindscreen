import os
import re
import requests

# ── HuggingFace Inference API ──────────────────────────────────────────────
# Uses the HF API so we don't load a 500MB model into memory on the server.
# mental/mental-roberta-base is a fill-mask model; we use j-hartmann/emotion
# (distilroberta, <200MB on HF servers) and map emotions → depression risk.
HF_API_URL = (
    "https://router.huggingface.co/hf-inference/models/"
    "j-hartmann/emotion-english-distilroberta-base"
)

# Emotion label → (risk_score 0-3, risk_label)
EMOTION_RISK_MAP = {
    "sadness":  (2, "moderate"),
    "fear":     (1, "mild"),
    "anger":    (1, "mild"),
    "disgust":  (2, "moderate"),
    "joy":      (0, "minimal"),
    "neutral":  (0, "minimal"),
    "surprise": (0, "minimal"),
}

print("ML Service initialised (HuggingFace Inference API mode — lightweight).")


def _get_hf_token() -> str | None:
    return os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")


def _query_hf_api(text: str) -> list | None:
    """Call the HF Inference API and return the classification results."""
    token = _get_hf_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": text, "options": {"wait_for_model": True}},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            # HF returns [[{label, score}, ...]] for text-classification
            if isinstance(data, list) and isinstance(data[0], list):
                return data[0]
            if isinstance(data, list) and isinstance(data[0], dict):
                return data
        print(f"HF API returned status {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"HF Inference API error: {e}")
    return None


def _build_lexical_indicators(text: str, risk_idx: int) -> list:
    """Return hand-written keyword indicators; these are not SHAP values."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    severe_kw  = {"suicide", "kill", "die", "hopeless", "end", "worthless", "pain"}
    moderate_kw = {"depressed", "anxious", "sad", "tired", "alone", "crying", "exhausted", "empty"}
    positive_kw = {"happy", "good", "great", "better", "hope", "peace", "calm", "enjoy"}

    result = []
    for w in set(words):
        if w in severe_kw:
            val = 0.35 if risk_idx >= 2 else -0.25
        elif w in moderate_kw:
            val = 0.22 if risk_idx >= 1 else -0.15
        elif w in positive_kw:
            val = -0.30 if risk_idx >= 1 else 0.20
        else:
            continue
        result.append({"word": w, "value": val})

    result.sort(key=lambda x: abs(x["value"]), reverse=True)
    return result[:6]


def _fallback_prediction(text: str) -> dict:
    """Keyword heuristic with negation resolution used when HF API is unreachable."""
    from services.negation_service import detect_crisis_intent
    crisis_info = detect_crisis_intent(text)
    words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
    moderate_kw = {"depressed", "anxious", "sad", "tired", "alone", "crying"}

    if crisis_info["is_crisis"]:
        risk, idx, conf = "severe", 3, 0.85
        probs = {"minimal": 0.05, "mild": 0.05, "moderate": 0.05, "severe": 0.85}
    elif any(k in words for k in moderate_kw):
        risk, idx, conf = "moderate", 2, 0.70
        probs = {"minimal": 0.10, "mild": 0.15, "moderate": 0.70, "severe": 0.05}
    else:
        risk, idx, conf = "minimal", 0, 0.90
        probs = {"minimal": 0.90, "mild": 0.05, "moderate": 0.03, "severe": 0.02}

    return {
        "risk_level": risk,
        "confidence": conf,
        "probabilities": probs,
        "shap_data": {"words": _build_lexical_indicators(text, idx)},
    }


def get_text_prediction(text: str) -> dict:
    """
    Primary prediction path:
    1. Query HF Inference API (emotion model → map to depression risk)
    2. Fallback to keyword heuristic if API fails
    """
    api_result = _query_hf_api(text)

    if api_result:
        # Find the top emotion
        top = max(api_result, key=lambda x: x["score"])
        emotion = top["label"].lower()
        score = top["score"]

        risk_idx, risk_label = EMOTION_RISK_MAP.get(emotion, (0, "minimal"))

        # Check crisis intent using linguistic negation and scope resolution
        from services.negation_service import detect_crisis_intent
        crisis_info = detect_crisis_intent(text)
        if crisis_info["is_crisis"]:
            risk_idx = max(risk_idx, 3)
            risk_label = "severe"

        # Build probability distribution around the predicted risk
        base = [0.1, 0.1, 0.1, 0.1]
        base[risk_idx] = score
        total = sum(base)
        probs_list = [v / total for v in base]
        probabilities = {
            "minimal":  round(probs_list[0], 4),
            "mild":     round(probs_list[1], 4),
            "moderate": round(probs_list[2], 4),
            "severe":   round(probs_list[3], 4),
        }

        print(f"HF API prediction: emotion={emotion}, risk={risk_label} ({score*100:.1f}%)")
        return {
            "risk_level":    risk_label,
            "confidence":    round(score, 4),
            "probabilities": probabilities,
            "shap_data":     {"words": _build_lexical_indicators(text, risk_idx)},
        }

    print("HF API unavailable — using keyword fallback.")
    return _fallback_prediction(text)
