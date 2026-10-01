import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.calibration_service import apply_temperature_scaling, compute_ece, compute_brier_score

print("=== TESTING CALIBRATION SERVICE ===")

# Test 1: Temperature scaling smoothing
raw_probs = {"minimal": 0.05, "mild": 0.10, "moderate": 0.15, "severe": 0.70}
calibrated = apply_temperature_scaling(raw_probs, temperature=1.3)
print(f"Raw probs       : {raw_probs}")
print(f"Calibrated (T=1.3): {calibrated}")
assert abs(sum(calibrated.values()) - 1.0) < 0.001, "Calibrated probabilities must sum to 1.0"
assert calibrated["severe"] < raw_probs["severe"], "T > 1 must soften overconfidence"
print("[PASS] Temperature scaling correctly softens overconfident top probability")

# Test 2: ECE computation
confidences = [0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50]
accuracies  = [1,    1,    1,    1,    0,    1,    0,    1,    0,    0]
ece, bins = compute_ece(confidences, accuracies, num_bins=5)
print(f"ECE Score: {ece} ({ece * 100:.1f}%)")
assert 0.0 <= ece <= 1.0, "ECE must be bounded in [0, 1]"
print("[PASS] Expected Calibration Error computation verified")

# Test 3: Brier Score
probs_matrix = [
    [0.7, 0.1, 0.1, 0.1],
    [0.1, 0.8, 0.05, 0.05],
    [0.1, 0.2, 0.6, 0.1],
    [0.05, 0.05, 0.1, 0.8]
]
targets = [0, 1, 2, 3] # Perfect matches
brier_perfect = compute_brier_score(probs_matrix, targets)
print(f"Brier Score (high concordance): {brier_perfect}")
assert brier_perfect < 0.5, "Concordant predictions must yield low Brier score"
print("[PASS] Brier Score computation verified")

print("\nAll calibration service sanity checks passed (100%)!")
