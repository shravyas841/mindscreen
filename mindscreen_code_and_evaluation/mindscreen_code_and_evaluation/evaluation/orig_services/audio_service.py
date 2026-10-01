import base64
from typing import Optional

# ── Audio Service ─────────────────────────────────────────────────────────────
#
# UPGRADED: Now accepts real acoustic features extracted by the browser-side
# Web Audio API (AudioFeatureExtractor in frontend/src/utils/audioFeatures.ts).
#
# Features extracted in the browser:
#   rms_mean         — mean RMS energy (0-1): average loudness
#   rms_std          — std-dev of RMS (0-1): energy variability (monotone voice = low)
#   zcr_mean         — mean zero-crossing rate (0-1): breathiness / voicing
#   spectral_centroid — normalised spectral centroid (0-1): voice brightness
#   spectral_rolloff  — normalised 85% rolloff (0-1): high-frequency energy
#   speaking_ratio   — fraction of voiced frames (0-1)
#
# Clinical mapping (based on depression speech literature: Cummins et al. 2015):
#   Depressed speech characteristics:
#     - Low RMS (reduced vocal effort)
#     - Low RMS std (monotone, flat affect)
#     - Low spectral centroid (muffled, low-brightness voice)
#     - Low speaking ratio (long silences, hesitancy)
#     - ZCR can be high (breathiness) or low (slurred)
#
# Legacy fallback: if no audio_features provided, falls back to Base64 size proxy.

import numpy as np


def get_audio_prediction(audio_base64: Optional[str] = None,
                         audio_features: Optional[dict] = None) -> dict:
    """
    Compute an acoustic risk score vector.

    Priority:
      1. audio_features dict (real Web Audio API features) — used if provided
      2. audio_base64 string (legacy payload-size fallback) — used otherwise
      3. No input — returns neutral baseline
    """
    if audio_features is not None:
        return _score_from_features(audio_features)

    if audio_base64:
        return _score_from_base64(audio_base64)

    # No audio provided — conservative neutral prior
    return _make_result("mild", 0.50, [0.25, 0.45, 0.20, 0.10])


# ── Real feature-based scoring ─────────────────────────────────────────────────

def _score_from_features(f: dict) -> dict:
    """
    Map 6 acoustic features to a 4-class risk distribution.

    Each feature contributes a depression score component; the components
    are combined into a single composite depression index (0-1), which is
    then mapped to the 4-class distribution.

    All weights and thresholds are design choices grounded in the speech
    depression literature; they are not learned from labeled data.
    """
    # Validate and clamp all features to [0, 1]
    rms_mean          = _clamp(f.get("rms_mean", 0.3))
    rms_std           = _clamp(f.get("rms_std", 0.1))
    zcr_mean          = _clamp(f.get("zcr_mean", 0.3))
    spectral_centroid = _clamp(f.get("spectral_centroid", 0.4))
    spectral_rolloff  = _clamp(f.get("spectral_rolloff", 0.4))
    speaking_ratio    = _clamp(f.get("speaking_ratio", 0.5))

    # ── Depression component scores ───────────────────────────────────────────
    # Each component ranges 0 (healthy/minimal) to 1 (depressed/severe).
    # Logic: low energy, monotone voice, low speaking ratio → depression signal.

    # Low energy → depression (inverted RMS mean)
    energy_score = 1.0 - rms_mean

    # Low variability → monotone affect (inverted RMS std)
    # Healthy speech: rms_std ≈ 0.15–0.35. Flat affect: rms_std < 0.08
    variability_score = 1.0 - min(rms_std / 0.25, 1.0)

    # Low spectral centroid → muffled, flat voice quality
    brightness_score = 1.0 - spectral_centroid

    # Low spectral rolloff → suppressed high-frequency energy
    rolloff_score = 1.0 - spectral_rolloff

    # Low speaking ratio → many silences and hesitations
    silence_score = 1.0 - speaking_ratio

    # ZCR: moderate ZCR is normal speech; very low (slurred) or very high (breathy)
    # both can indicate distress. Distance from healthy midpoint (0.25):
    zcr_deviation = abs(zcr_mean - 0.25) / 0.25
    zcr_score = min(zcr_deviation, 1.0)

    # ── Composite depression index (weighted sum over all 6 features, in [0, 1]) ──
    # Weights reflect relative clinical informativeness (Cummins et al. 2015):
    #   [energy, variability, brightness, rolloff, silence, zcr]
    weights = np.array([0.20, 0.20, 0.15, 0.15, 0.20, 0.10])
    components = np.array([energy_score, variability_score,
                           brightness_score, rolloff_score, silence_score, zcr_score])
    depression_index = float(np.dot(weights, components))  # [0, 1]

    # ── Map composite index to 4-class distribution ───────────────────────────
    # Boundaries are conservative: err toward flagging moderate rather than missing it
    if depression_index < 0.25:
        probs = _interpolate(depression_index, 0.0, 0.25,
                             [0.80, 0.15, 0.04, 0.01],
                             [0.50, 0.35, 0.12, 0.03])
        label, conf = "minimal", max(probs)
    elif depression_index < 0.45:
        probs = _interpolate(depression_index, 0.25, 0.45,
                             [0.50, 0.35, 0.12, 0.03],
                             [0.15, 0.55, 0.25, 0.05])
        label, conf = "mild", max(probs)
    elif depression_index < 0.65:
        probs = _interpolate(depression_index, 0.45, 0.65,
                             [0.15, 0.55, 0.25, 0.05],
                             [0.05, 0.20, 0.60, 0.15])
        label, conf = "moderate", max(probs)
    else:
        probs = _interpolate(depression_index, 0.65, 1.0,
                             [0.05, 0.20, 0.60, 0.15],
                             [0.02, 0.08, 0.35, 0.55])
        label, conf = "severe", max(probs)

    return _make_result(label, round(conf, 3), [round(p, 4) for p in probs])


# ── Legacy Base64 size fallback ────────────────────────────────────────────────

def _score_from_base64(audio_base64: str) -> dict:
    """
    LEGACY: payload-size proxy used when browser does not send audio_features.
    Not a validated acoustic measurement.
    """
    try:
        encoded = audio_base64.split(",", 1)[1] if "," in audio_base64 else audio_base64
        audio_bytes = base64.b64decode(encoded)
        size_kb = len(audio_bytes) / 1024

        if size_kb < 5:
            return _make_result("moderate", 0.55, [0.15, 0.20, 0.55, 0.10])
        elif size_kb < 30:
            return _make_result("mild",    0.55, [0.20, 0.55, 0.20, 0.05])
        else:
            return _make_result("minimal", 0.65, [0.65, 0.20, 0.10, 0.05])

    except Exception as e:
        print(f"Audio (base64) fallback error: {e}")
        return _make_result("minimal", 0.50, [0.55, 0.25, 0.15, 0.05])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_result(label: str, confidence: float, probs_list: list) -> dict:
    keys = ["minimal", "mild", "moderate", "severe"]
    return {
        "risk_level":  label,
        "confidence":  confidence,
        "probabilities": dict(zip(keys, probs_list)),
    }


def _interpolate(x: float, lo: float, hi: float,
                 probs_lo: list, probs_hi: list) -> list:
    """Linear interpolation between two probability vectors."""
    t = (x - lo) / (hi - lo)
    interpolated = [(1 - t) * a + t * b for a, b in zip(probs_lo, probs_hi)]
    total = sum(interpolated)
    return [v / total for v in interpolated]  # renormalise


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v) if v is not None else 0.0))
