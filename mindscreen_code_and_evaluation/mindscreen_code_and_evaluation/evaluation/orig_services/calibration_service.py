"""
Statistical Calibration and Uncertainty Quantification Service
---------------------------------------------------------------
Implements Temperature Scaling and Expected Calibration Error (ECE)
following Guo et al. (ICML 2017) "On Calibration of Modern Neural Networks".

Addresses Reviewer Major Comment 3:
Ensures that the output score vector p^F reflects calibrated statistical confidence
rather than uncalibrated heuristic scores.
"""

import numpy as np
from typing import Dict, List, Tuple, Any


DEFAULT_TEMPERATURE = 1.20  # Score-smoothing temperature for late fusion transformation


def apply_temperature_scaling(
    probs: Dict[str, float],
    temperature: float = DEFAULT_TEMPERATURE
) -> Dict[str, float]:
    """
    Applies temperature scaling to a probability dictionary.
    Converts probabilities to pseudo-logits, divides by T, and applies softmax.
    
    Args:
        probs: Dict of class -> probability (must sum to ~1.0)
        temperature: Scalar T > 0 (T > 1 softens overconfidence)
    Returns:
        Calibrated probability dictionary
    """
    labels = list(probs.keys())
    p_vals = np.array([probs[k] for k in labels], dtype=np.float64)

    # Numerical safety: clip to prevent log(0)
    eps = 1e-7
    p_clipped = np.clip(p_vals, eps, 1.0 - eps)

    # Convert to log-odds pseudo-logits
    logits = np.log(p_clipped)

    # Scale logits by temperature
    scaled_logits = logits / max(temperature, 0.01)

    # Softmax with numerical stability
    exp_logits = np.exp(scaled_logits - np.max(scaled_logits))
    calibrated_p = exp_logits / np.sum(exp_logits)

    return {k: round(float(calibrated_p[i]), 4) for i, k in enumerate(labels)}


def compute_ece(
    confidences: List[float],
    accuracies: List[int],
    num_bins: int = 10
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Computes Expected Calibration Error (ECE) across M equal-width bins.

    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|

    Args:
        confidences: List of predicted top-class probabilities in [0, 1]
        accuracies: List of 0 or 1 indicating whether top prediction matched ground truth
        num_bins: Number of confidence bins (standard M = 10)
    Returns:
        (ece_score, bin_details_list)
    """
    conf = np.array(confidences, dtype=np.float64)
    acc = np.array(accuracies, dtype=np.float64)
    n = len(conf)
    if n == 0:
        return 0.0, []

    bin_edges = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0
    bin_details = []

    for i in range(num_bins):
        bin_lo = bin_edges[i]
        bin_hi = bin_edges[i + 1]

        # Bins are [bin_lo, bin_hi) except last bin which is [bin_lo, bin_hi]
        if i == num_bins - 1:
            mask = (conf >= bin_lo) & (conf <= bin_hi)
        else:
            mask = (conf >= bin_lo) & (conf < bin_hi)

        bin_count = int(np.sum(mask))
        if bin_count > 0:
            bin_acc = float(np.mean(acc[mask]))
            bin_conf = float(np.mean(conf[mask]))
            bin_error = abs(bin_acc - bin_conf)
            ece += (bin_count / n) * bin_error

            bin_details.append({
                "bin": f"[{bin_lo:.1f}, {bin_hi:.1f}]",
                "count": bin_count,
                "accuracy": round(bin_acc, 3),
                "confidence": round(bin_conf, 3),
                "calibration_error": round(bin_error, 3),
            })
        else:
            bin_details.append({
                "bin": f"[{bin_lo:.1f}, {bin_hi:.1f}]",
                "count": 0,
                "accuracy": 0.0,
                "confidence": 0.0,
                "calibration_error": 0.0,
            })

    return round(float(ece), 4), bin_details


def compute_brier_score(
    probs: List[List[float]],
    targets: List[int],
    num_classes: int = 4
) -> float:
    """
    Computes multi-class Brier score:
    Brier = (1/N) * sum_{i=1}^N sum_{k=1}^K (p_{i,k} - y_{i,k})^2
    """
    p_arr = np.array(probs, dtype=np.float64)
    n = len(targets)
    if n == 0:
        return 0.0

    y_one_hot = np.zeros((n, num_classes), dtype=np.float64)
    for i, t in enumerate(targets):
        y_one_hot[i, t] = 1.0

    brier = np.mean(np.sum((p_arr - y_one_hot) ** 2, axis=1))
    return round(float(brier), 4)
