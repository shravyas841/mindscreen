"""Generate deterministic, implementation-grounded submission evidence.

The script does not call hosted APIs.  It exercises the production PHQ, audio,
fusion, HRE, temperature, and crisis-language functions with a fixed local text
branch so results remain reproducible without network access.
"""

from __future__ import annotations

import json
import os
import platform
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

from services import fusion_service
from services.audio_service import get_audio_prediction
from services.negation_service import detect_crisis_intent
from services.phq_service import calculate_phq_score


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "benchmarks" / "submission_evidence.json"


def deterministic_text_prediction(_text: str) -> dict:
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


fusion_service.get_text_prediction = deterministic_text_prediction

NEUTRAL_AUDIO = {
    "rms_mean": 0.30,
    "rms_std": 0.10,
    "zcr_mean": 0.30,
    "spectral_centroid": 0.40,
    "spectral_rolloff": 0.40,
    "speaking_ratio": 0.50,
}

HRE_CASES = {
    "HRE-1-high-score-only": {
        "answers": [3, 3, 3, 3, 2, 2, 2, 2, 0],
        "text": "I am completing the questionnaire.",
        "expected_trigger": "PHQ-9 total >= 20 only",
    },
    "HRE-2-item9": {
        "answers": [0, 0, 0, 0, 0, 0, 0, 0, 1],
        "text": "I am completing the questionnaire.",
        "expected_trigger": "PHQ-9 Item 9 > 0",
    },
    "HRE-3-text": {
        "answers": [0] * 9,
        "text": "I want to die.",
        "expected_trigger": "affirmative self-directed crisis language",
    },
    "HRE-4-no-trigger": {
        "answers": [0] * 9,
        "text": "I had an ordinary day.",
        "expected_trigger": "none",
    },
}

CRISIS_CORPUS = [
    ("A1", "I want to die.", True, "affirmative"),
    ("A2", "I want to end my life.", True, "affirmative"),
    ("A3", "I don't want to be alive anymore.", True, "affirmative"),
    ("A4", "I no longer want to live.", True, "affirmative"),
    ("A5", "I plan to overdose.", True, "affirmative"),
    ("A6", "I was killing it at work, but now I want to die.", True, "mixed-clause"),
    ("A7", "My friend abandoned me and now I want to die.", True, "mixed-clause"),
    ("A8", "I am not okay and I want to die.", True, "unrelated-negation"),
    ("N1", "I don't want to die.", False, "negation"),
    ("N2", "I do not want to kill myself.", False, "negation"),
    ("N3", "I would never commit suicide.", False, "negation"),
    ("T1", "My friend said they want to die.", False, "third-party"),
    ("T2", "She told me she wants to kill herself.", False, "third-party"),
    ("Q1", 'My friend said "I want to die."', False, "quotation"),
    ("I1", "I was killing it at work today.", False, "idiom"),
    ("I2", "That exam killed me.", False, "idiom"),
    ("I3", "We were trying to kill time.", False, "idiom"),
]


def run_hre_cases() -> dict:
    output = {}
    for name, case in HRE_CASES.items():
        result = fusion_service.get_fused_prediction(
            case["answers"], case["text"], audio_features=NEUTRAL_AUDIO
        )
        output[name] = {
            "inputs": case,
            "phq_total": sum(case["answers"]),
            "item9": case["answers"][8],
            "risk_level": result["risk_level"],
            "priority_score": round(result["priority_score"], 4),
            "crisis_flag": result["crisis_flag"],
            "resource_display_flag": result["resource_display_flag"],
            "audio_available": result["audio_available"],
            "score_distribution": result["probabilities"],
        }
    return output


def run_crisis_corpus() -> dict:
    trace = []
    naive_terms = ("die", "kill", "suicide", "self harm", "self-harm", "overdose")
    for case_id, text, expected, category in CRISIS_CORPUS:
        scoped = detect_crisis_intent(text)["is_crisis"]
        naive = any(term in text.lower() for term in naive_terms)
        trace.append({
            "id": case_id,
            "text": text,
            "category": category,
            "expected_crisis": expected,
            "naive_flag": naive,
            "detector_flag": scoped,
        })

    positives = sum(row["expected_crisis"] for row in trace)
    negatives = len(trace) - positives

    def metrics(key: str) -> dict:
        tp = sum(row[key] and row["expected_crisis"] for row in trace)
        tn = sum((not row[key]) and (not row["expected_crisis"]) for row in trace)
        fp = sum(row[key] and (not row["expected_crisis"]) for row in trace)
        fn = sum((not row[key]) and row["expected_crisis"] for row in trace)
        return {
            "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "affirmative_detection_rate": tp / positives,
            "false_positive_rate": fp / negatives,
            "accuracy": (tp + tn) / len(trace),
        }

    return {
        "description": "Constructed rule-verification corpus; not a clinical dataset.",
        "case_count": len(trace),
        "trace": trace,
        "naive_metrics": metrics("naive_flag"),
        "detector_metrics": metrics("detector_flag"),
    }


def profile(func, *args, runs: int = 50, warmup: int = 10) -> dict:
    for _ in range(warmup):
        func(*args)
    tracemalloc.start()
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        func(*args)
        times.append((time.perf_counter() - start) * 1000.0)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    ordered = sorted(times)
    p95 = float(np.percentile(ordered, 95))
    return {
        "runs": runs,
        "warmup": warmup,
        "mean_ms": round(statistics.fmean(times), 6),
        "p95_ms": round(p95, 6),
        "min_ms": round(min(times), 6),
        "max_ms": round(max(times), 6),
        "peak_python_heap_kb": round(peak / 1024, 3),
        "raw_times_ms": [round(value, 6) for value in times],
    }


def local_fusion() -> dict:
    return fusion_service.get_fused_prediction(
        [1, 1, 1, 1, 0, 1, 1, 0, 0],
        "I had an ordinary day.",
        audio_features=NEUTRAL_AUDIO,
    )


def run_latency() -> dict:
    return {
        "measurement_scope": (
            "In-process deterministic Python functions only; excludes HTTP, database, "
            "browser feature extraction, hosted APIs, and network round trips."
        ),
        "environment": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unreported",
            "python_version": sys.version,
            "timer": "time.perf_counter",
            "memory": "tracemalloc peak Python-managed heap",
        },
        "components": {
            "phq9_mapping": profile(calculate_phq_score, [1, 1, 1, 1, 0, 1, 1, 0, 0]),
            "acoustic_scoring": profile(get_audio_prediction, None, NEUTRAL_AUDIO),
            "crisis_language_gate": profile(detect_crisis_intent, "I want to die."),
            "local_fusion_pipeline": profile(local_fusion),
        },
    }


def main() -> None:
    evidence = {
        "evidence_version": 1,
        "network_calls": False,
        "text_branch": "fixed deterministic local score vector; hosted NLP excluded",
        "hre_scenarios": run_hre_cases(),
        "crisis_language_evaluation": run_crisis_corpus(),
        "local_latency": run_latency(),
    }
    OUTPUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(json.dumps({
        "hre_scenarios": evidence["hre_scenarios"],
        "crisis_metrics": evidence["crisis_language_evaluation"]["detector_metrics"],
        "latency_summary": {
            key: {k: value[k] for k in ("mean_ms", "p95_ms", "peak_python_heap_kb")}
            for key, value in evidence["local_latency"]["components"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
