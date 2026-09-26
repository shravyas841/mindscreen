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
WEIGHT_OUTPUT = ROOT / "benchmarks" / "current_weight_sensitivity.json"


DEFAULT_TEXT_VECTOR = {
    "minimal": 0.70,
    "mild": 0.15,
    "moderate": 0.10,
    "severe": 0.05,
}

SENSITIVITY_TEXT_VECTORS = {
    "[profile:minimal]": {"minimal": 0.80, "mild": 0.10, "moderate": 0.07, "severe": 0.03},
    "[profile:moderate]": {"minimal": 0.05, "mild": 0.10, "moderate": 0.70, "severe": 0.15},
}


def deterministic_text_prediction(text: str) -> dict:
    probabilities = SENSITIVITY_TEXT_VECTORS.get(text, DEFAULT_TEXT_VECTOR)
    risk_level = max(probabilities, key=probabilities.get)
    return {
        "risk_level": risk_level,
        "confidence": probabilities[risk_level],
        "probabilities": probabilities,
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

LOW_RISK_AUDIO = {
    "rms_mean": 0.65,
    "rms_std": 0.25,
    "zcr_mean": 0.25,
    "spectral_centroid": 0.65,
    "spectral_rolloff": 0.70,
    "speaking_ratio": 0.90,
}

ELEVATED_AUDIO = {
    "rms_mean": 0.05,
    "rms_std": 0.02,
    "zcr_mean": 0.05,
    "spectral_centroid": 0.15,
    "spectral_rolloff": 0.20,
    "speaking_ratio": 0.20,
}

WEIGHT_CONFIGURATIONS = {
    "equal": {"text": 1 / 3, "audio": 1 / 3, "phq": 1 / 3},
    "text_dominant": {"text": 0.60, "audio": 0.20, "phq": 0.20},
    "audio_dominant": {"text": 0.20, "audio": 0.60, "phq": 0.20},
    "phq_dominant": {"text": 0.20, "audio": 0.20, "phq": 0.60},
    "current_production": dict(fusion_service.DEFAULT_FUSION_WEIGHTS),
}

SENSITIVITY_CASES = {
    "C1-concordant-minimal": {
        "answers": [0] * 9,
        "text": "[profile:minimal]",
        "audio_features": LOW_RISK_AUDIO,
        "description": "Constructed low-score agreement across all three modalities.",
    },
    "C2-text-led-moderate": {
        "answers": [0] * 9,
        "text": "[profile:moderate]",
        "audio_features": LOW_RISK_AUDIO,
        "description": "Constructed text-led discordance without an HRE trigger.",
    },
    "C3-audio-led-elevated": {
        "answers": [0] * 9,
        "text": "[profile:minimal]",
        "audio_features": ELEVATED_AUDIO,
        "description": "Constructed audio-led discordance without an HRE trigger.",
    },
    "C4-phq-led-moderate": {
        "answers": [2, 2, 2, 2, 2, 2, 1, 1, 0],
        "text": "[profile:minimal]",
        "audio_features": LOW_RISK_AUDIO,
        "description": "Constructed PHQ-led discordance at total score 14.",
    },
    "C5-missing-audio": {
        "answers": [1, 1, 1, 1, 1, 1, 0, 0, 0],
        "text": "[profile:moderate]",
        "audio_features": None,
        "description": "Constructed missing-audio case using the production prior.",
    },
    "C6-high-score-HRE": {
        "answers": [3, 3, 3, 3, 2, 2, 2, 2, 0],
        "text": "[profile:minimal]",
        "audio_features": LOW_RISK_AUDIO,
        "description": "High PHQ total with Item 9 zero; HRE is reported separately.",
    },
    "C7-item9-HRE": {
        "answers": [0, 0, 0, 0, 0, 0, 0, 0, 1],
        "text": "[profile:minimal]",
        "audio_features": None,
        "description": "Item 9 endorsement with missing audio; HRE is reported separately.",
    },
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


def run_weight_sensitivity() -> dict:
    cases = {}
    for case_name, case in SENSITIVITY_CASES.items():
        configurations = {}
        for config_name, weights in WEIGHT_CONFIGURATIONS.items():
            result = fusion_service.get_fused_prediction(
                case["answers"],
                case["text"],
                audio_features=case["audio_features"],
                weights=weights,
            )
            raw_label = max(result["raw_probabilities"], key=result["raw_probabilities"].get)
            configurations[config_name] = {
                "weights": weights,
                "raw_fusion": {
                    "score_vector": result["raw_probabilities"],
                    "winning_tier": raw_label,
                    "winning_score": round(result["raw_probabilities"][raw_label], 4),
                },
                "temperature_transformed": {
                    "score_vector": result["probabilities"],
                    "winning_tier": max(result["probabilities"], key=result["probabilities"].get),
                    "winning_score": round(result["base_score"], 4),
                },
                "post_hre": {
                    "risk_level": result["risk_level"],
                    "priority_score": round(result["priority_score"], 4),
                    "crisis_flag": result["crisis_flag"],
                    "resource_display_flag": result["resource_display_flag"],
                },
                "audio_available": result["audio_available"],
            }

        raw_tiers = {
            value["raw_fusion"]["winning_tier"] for value in configurations.values()
        }
        cases[case_name] = {
            "description": case["description"],
            "inputs": {
                "phq_answers": case["answers"],
                "phq_total": sum(case["answers"]),
                "item9": case["answers"][8],
                "text_score_vector": deterministic_text_prediction(case["text"])["probabilities"],
                "audio_features": case["audio_features"],
                "missing_audio_policy": (
                    [0.25, 0.45, 0.20, 0.10] if case["audio_features"] is None else None
                ),
            },
            "raw_tier_changes_across_configurations": len(raw_tiers) > 1,
            "configurations": configurations,
        }

    return {
        "description": (
            "Deterministic sensitivity analysis over constructed modality-score cases; "
            "not a labeled dataset, accuracy study, or weight optimization."
        ),
        "reported_metrics": [
            "raw fused score vector and winning tier",
            "temperature-transformed score vector and winning tier",
            "post-HRE tier, priority score, crisis flag, and resource flag",
            "whether the raw winning tier changes across weight configurations",
        ],
        "held_constant": (
            "Current PHQ mapping, audio heuristic or documented missing-audio prior, "
            "temperature 1.20, crisis gate, and HRE rules."
        ),
        "configurations": WEIGHT_CONFIGURATIONS,
        "cases": cases,
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
    weight_sensitivity = run_weight_sensitivity()
    WEIGHT_OUTPUT.write_text(json.dumps(weight_sensitivity, indent=2), encoding="utf-8")
    changed_cases = [
        name for name, case in weight_sensitivity["cases"].items()
        if case["raw_tier_changes_across_configurations"]
    ]
    evidence = {
        "evidence_version": 2,
        "network_calls": False,
        "text_branch": "fixed deterministic local score vector; hosted NLP excluded",
        "evidence_scope": {
            "current_implementation": "implementation_facts",
            "current_deterministic_tests": [
                "backend/tests/test_safety_logic.py",
                "frontend/src/utils/audioFeatures.test.ts",
                "frontend/src/api/routes.test.ts",
            ],
            "test_execution_note": (
                "This generator does not execute test runners; use pytest and npm test "
                "and report their results separately."
            ),
            "current_constructed_evidence": [
                "hre_scenarios",
                "crisis_language_evaluation",
                "benchmarks/current_weight_sensitivity.json",
            ],
            "historical_obsolete_artifacts": [
                "benchmarks/p1_p5_sensitivity_raw.json",
                "benchmarks/raw_latency_measurements.json",
                "benchmarks/latency_raw_trace.json",
                "benchmarks/hre_masking_scenarios_raw.json",
                "benchmarks/crisis_disambiguation_trace.json",
            ],
        },
        "implementation_facts": {
            "production_fusion_weights": fusion_service.DEFAULT_FUSION_WEIGHTS,
            "temperature": 1.20,
            "temperature_status": "heuristic score transformation; not statistically calibrated",
            "missing_audio_prior": [0.25, 0.45, 0.20, 0.10],
            "missing_audio_weight_is_renormalized": False,
            "very_short_audio_threshold_frames": 5,
            "very_short_audio_representation": "missing; client submits null descriptors",
            "raw_audio_in_assessment_payload": False,
            "hre_triggers": [
                "PHQ-9 total >= 20",
                "PHQ-9 Item 9 > 0",
                "affirmative self-directed crisis language",
            ],
            "crisis_flag_triggers": [
                "PHQ-9 Item 9 > 0",
                "affirmative self-directed crisis language",
            ],
        },
        "hre_scenarios": run_hre_cases(),
        "crisis_language_evaluation": run_crisis_corpus(),
        "weight_sensitivity": {
            "artifact": "benchmarks/current_weight_sensitivity.json",
            "description": weight_sensitivity["description"],
            "case_count": len(weight_sensitivity["cases"]),
            "configurations": weight_sensitivity["configurations"],
            "cases_with_raw_tier_changes": changed_cases,
            "accuracy_or_optimal_weight_claimed": False,
        },
        "local_latency": run_latency(),
    }
    OUTPUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Wrote {WEIGHT_OUTPUT}")
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
