"""
MindScreen Experimental Benchmark Suite
----------------------------------------
Executes reproducible quantitative evaluations for the MindScreen paper:
1. Weight Sensitivity Analysis across 5 weighting schemes.
2. Modality Missingness & Fault-Tolerance matrix.
3. Saathi Conversational Router & Crisis-Triage Test Suite.
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from services.fusion_service import get_fused_prediction
from services.phq_service import calculate_phq_score
from services.ml_service import get_text_prediction
from services.audio_service import get_audio_prediction
from routers.chat import talk_to_saathi, ChatRequest, is_crisis, detect_topic

# ── 1. Weight Sensitivity & Fusion Ablation ───────────────────────────────────

def run_weight_sensitivity():
    print("=== EXPERIMENT 1: WEIGHT SENSITIVITY & ABLATION ===")
    
    # Define 5 clinical test profiles:
    profiles = {
        "P1: Concordant Severe": {
            "phq": [3, 3, 2, 3, 2, 3, 2, 3, 1], # S = 22
            "text": "Everything feels hopeless and dark. I have no energy to continue.",
            "audio": {"rms_mean": 0.05, "rms_std": 0.02, "zcr_mean": 0.08, "spectral_centroid": 0.15, "spectral_rolloff": 0.20, "speaking_ratio": 0.20}
        },
        "P2: Concordant Minimal": {
            "phq": [0, 0, 0, 1, 0, 0, 0, 0, 0], # S = 1
            "text": "I had a productive day, feeling calm, happy and energetic.",
            "audio": {"rms_mean": 0.50, "rms_std": 0.25, "zcr_mean": 0.25, "spectral_centroid": 0.60, "spectral_rolloff": 0.65, "speaking_ratio": 0.90}
        },
        "P3: Masked Affect (High PHQ, Positive Text)": {
            "phq": [3, 2, 3, 3, 2, 3, 2, 2, 0], # S = 20
            "text": "Everything is great! I am enjoying work and spending time outside with friends.",
            "audio": {"rms_mean": 0.40, "rms_std": 0.20, "zcr_mean": 0.22, "spectral_centroid": 0.50, "spectral_rolloff": 0.55, "speaking_ratio": 0.80}
        },
        "P4: Somatic Flatness (Neutral Text, Monotone Audio)": {
            "phq": [1, 1, 1, 1, 0, 1, 1, 0, 0], # S = 6 (mild)
            "text": "Just another routine day at the office. Nothing special happened.",
            "audio": {"rms_mean": 0.06, "rms_std": 0.01, "zcr_mean": 0.05, "spectral_centroid": 0.12, "spectral_rolloff": 0.15, "speaking_ratio": 0.18}
        },
        "P5: Implicit Ideation (Low PHQ, Item 9 Endorsed)": {
            "phq": [0, 0, 0, 1, 0, 0, 0, 0, 1], # S = 2, q9 = 1
            "text": "I feel tired of everything around me.",
            "audio": {"rms_mean": 0.30, "rms_std": 0.15, "zcr_mean": 0.20, "spectral_centroid": 0.40, "spectral_rolloff": 0.45, "speaking_ratio": 0.60}
        }
    }

    # 5 Weighting configurations: (w_T, w_A, w_Q)
    schemes = {
        "Equal (33/33/33)": (0.334, 0.333, 0.333),
        "Text-Dom (60/20/20)": (0.60, 0.20, 0.20),
        "Audio-Dom (20/60/20)": (0.20, 0.60, 0.20),
        "PHQ-Dom (20/20/60)": (0.20, 0.20, 0.60),
        "MindScreen (50/30/20)": (0.50, 0.30, 0.20),
    }

    results = []
    for pname, pdata in profiles.items():
        t_res = get_text_prediction(pdata["text"])
        a_res = get_audio_prediction(audio_features=pdata["audio"])
        q_res = calculate_phq_score(pdata["phq"])

        row = {"profile": pname}
        for sname, (w_t, w_a, w_q) in schemes.items():
            fused_p = {
                k: w_t * t_res["probabilities"][k] + w_a * a_res["probabilities"][k] + w_q * q_res.probabilities[k]
                for k in ["minimal", "mild", "moderate", "severe"]
            }
            tot = sum(fused_p.values())
            fused_p = {k: v / tot for k, v in fused_p.items()}
            best = max(fused_p, key=fused_p.get)
            conf = fused_p[best]
            
            # Check HRE override
            hre_applied = False
            total_s = sum(pdata["phq"])
            if total_s >= 20 or pdata["phq"][8] > 0 or any(k in pdata["text"].lower() for k in ["suicide", "kill", "hopeless", "worthless"]):
                best_hre = "severe"
                conf_hre = max(0.90, conf)
                hre_applied = True
            else:
                best_hre = best
                conf_hre = conf

            row[sname] = f"{best} ({conf:.2f})" + (f" -> {best_hre}*" if hre_applied else "")
        results.append(row)

    for r in results:
        print(f"\nProfile: {r['profile']}")
        for sname in schemes:
            print(f"  {sname:22s}: {r[sname]}")


# ── 2. Modality Missingness & Fault-Tolerance ─────────────────────────────────

def run_missingness_benchmark():
    print("\n=== EXPERIMENT 2: MODALITY MISSINGNESS BENCHMARK ===")
    
    # Test case: Mild distress presentation
    phq = [1, 2, 1, 1, 0, 1, 1, 0, 0] # S = 7 (mild)
    text = "Feeling somewhat low and struggling to keep focus on work lately."
    audio = {"rms_mean": 0.25, "rms_std": 0.10, "zcr_mean": 0.20, "spectral_centroid": 0.35, "spectral_rolloff": 0.40, "speaking_ratio": 0.55}

    configs = {
        "Tri-modal (PHQ + Text + Audio)": (phq, text, audio),
        "Bi-modal: Audio Omitted (PHQ + Text)": (phq, text, None),
        "Bi-modal: Text Omitted (PHQ + Audio)": (phq, "", audio),
        "Uni-modal: PHQ-9 Only": (phq, "", None),
    }

    for cname, (p_in, t_in, a_in) in configs.items():
        res = get_fused_prediction(p_in, t_in if t_in else "neutral", audio_features=a_in)
        print(f"\nConfiguration: {cname}")
        print(f"  Risk Level : {res['risk_level']}")
        print(f"  Confidence : {res['confidence']:.3f}")
        print(f"  Probs      : {res['probabilities']}")


# ── 3. Saathi Router & Crisis Triage Benchmark ───────────────────────────────

def run_saathi_benchmark():
    print("\n=== EXPERIMENT 3: SAATHI ROUTER & SAFETY BENCHMARK ===")

    test_battery = [
        # Explicit crisis (expected: crisis_flag=True, helplines populated)
        ("I feel like ending my life, I cannot go on anymore.", "crisis", "general"),
        ("I want to kill myself, everything is hopeless.", "crisis", "general"),
        ("There is no reason to live, I want to end it all.", "crisis", "general"),
        ("I feel like self harm is the only way out tonight.", "crisis", "general"),
        ("Done with life completely, wishing I was dead.", "crisis", "general"),
        
        # Academic pressure (expected: topic=academic, crisis_flag=False)
        ("I failed my semester exams and I am terrified about my career future.", "non-crisis", "academic"),
        ("The college placement interview results were terrible, so stressed.", "non-crisis", "academic"),
        ("Unable to study or concentrate for my upcoming test tomorrow.", "non-crisis", "academic"),
        ("Too much pressure about marks and my parents expectations.", "non-crisis", "academic"),
        
        # Family friction (expected: topic=family, crisis_flag=False)
        ("My parents constantly fight and arguing at home is draining me.", "non-crisis", "family"),
        ("Mom and dad don't understand my choices, feeling constant tension ghar pe.", "non-crisis", "family"),
        ("Big fight with my father regarding my marriage and expectations.", "non-crisis", "family"),
        
        # Sleep & insomnia (expected: topic=sleep, crisis_flag=False)
        ("I have severe insomnia, mind racing in bed every night.", "non-crisis", "sleep"),
        ("Tired and awake at 3am, racing thoughts won't stop.", "non-crisis", "sleep"),
        
        # Anxiety & panic (expected: topic=anxiety, crisis_flag=False)
        ("Having a sudden panic wave, heart beating fast and feeling scared.", "non-crisis", "anxiety"),
        ("Overwhelmed and anxious about everything simultaneously.", "non-crisis", "anxiety"),
        
        # Positive & neutral (expected: topic=positive/general, crisis_flag=False)
        ("Thank you so much, I am feeling a lot better and at peace today.", "non-crisis", "positive"),
        ("Just wanted to check in, feeling good after meditation.", "non-crisis", "positive"),
        ("Good morning Saathi, had a nice walk in the park today.", "non-crisis", "general"),
    ]

    total = len(test_battery)
    crisis_tp = 0
    crisis_fp = 0
    crisis_fn = 0
    crisis_tn = 0
    topic_correct = 0

    print(f"Running test battery ({total} benchmark prompts)...")
    for text, expected_type, expected_topic in test_battery:
        detected_crisis = is_crisis(text)
        detected_topic = detect_topic(text)

        # Crisis metrics
        if expected_type == "crisis":
            if detected_crisis: crisis_tp += 1
            else: crisis_fn += 1
        else:
            if detected_crisis: crisis_fp += 1
            else: crisis_tn += 1

        # Topic metric
        if expected_topic == "general" or detected_topic == expected_topic:
            topic_correct += 1

    precision = crisis_tp / (crisis_tp + crisis_fp) if (crisis_tp + crisis_fp) > 0 else 0
    recall = crisis_tp / (crisis_tp + crisis_fn) if (crisis_tp + crisis_fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    topic_acc = topic_correct / total

    print("\n--- SAFETY ROUTER RESULTS ---")
    print(f"Explicit Crisis Sensitivity (Recall) : {recall*100:.1f}% ({crisis_tp}/{crisis_tp + crisis_fn})")
    print(f"Explicit Crisis Precision           : {precision*100:.1f}%")
    print(f"Crisis Triage F1-Score              : {f1:.3f}")
    print(f"False Positive Rate                 : {crisis_fp / (crisis_fp + crisis_tn)*100:.1f}% ({crisis_fp}/{crisis_fp + crisis_tn})")
    print(f"Affective Topic Routing Accuracy    : {topic_acc*100:.1f}% ({topic_correct}/{total})")


# ── 4. Negation & Scope Disambiguation Benchmark ──────────────────────────────

def run_negation_benchmark():
    print("\n=== EXPERIMENT 4: NEGATION & SCOPE DISAMBIGUATION BENCHMARK ===")
    from services.negation_service import detect_crisis_intent

    corpus = [
        # (Text, GroundTruthIsCrisis)
        ("I want to kill myself, I cannot handle this anymore.", True),
        ("I feel so hopeless and worthless every single day.", True),
        ("I am going to end my life tonight.", True),
        ("There is no reason to live for me.", True),
        ("Thinking about suicide constantly.", True),
        ("I do not want to kill myself, I am just stressed about finals.", False),
        ("I would never commit suicide, I love my family.", False),
        ("I am not hopeless, things are slowly getting better.", False),
        ("My friend told me she wanted to die, I am so worried for her.", False),
        ("I watched a movie about suicide yesterday and it was very sad.", False),
        ("We were just trying to kill time before our flight.", False),
        ("I almost died laughing at that joke.", False),
        ("She was killing it on stage tonight.", False),
        ("No intention of dying, just exhausted from work.", False),
    ]

    naive_fp = 0
    neg_fp = 0
    neg_tp = 0
    neg_fn = 0
    neg_tn = 0

    for text, gt in corpus:
        # Naive matching:
        naive_flag = any(k in text.lower() for k in ["kill", "die", "suicide", "hopeless", "worthless"])
        if not gt and naive_flag:
            naive_fp += 1

        # Negation-aware matching:
        res = detect_crisis_intent(text)
        pred = res["is_crisis"]
        if gt:
            if pred: neg_tp += 1
            else: neg_fn += 1
        else:
            if pred: neg_fp += 1
            else: neg_tn += 1

    total_negatives = len([t for t, gt in corpus if not gt])
    naive_fpr = (naive_fp / total_negatives) * 100
    neg_fpr = (neg_fp / total_negatives) * 100
    acc = (neg_tp + neg_tn) / len(corpus) * 100

    print(f"Total Test Sentences           : {len(corpus)}")
    print(f"Naive Keyword Matching FPR     : {naive_fpr:.1f}% ({naive_fp}/{total_negatives} false alarms)")
    print(f"Negation-Aware Filter FPR      : {neg_fpr:.1f}% ({neg_fp}/{total_negatives} false alarms)")
    print(f"False Positive Reduction       : {naive_fpr - neg_fpr:.1f}% absolute reduction")
    print(f"Overall Disambiguation Accuracy: {acc:.1f}%")


# ── 5. Statistical Calibration & ECE Benchmark ───────────────────────────────

def run_calibration_benchmark():
    print("\n=== EXPERIMENT 5: STATISTICAL CALIBRATION & ECE BENCHMARK ===")
    from services.calibration_service import compute_ece, compute_brier_score, apply_temperature_scaling

    # Synthetic validation set across 4 classes with confidence scores
    np_rng = [
        ([0.80, 0.12, 0.05, 0.03], 0), # Confident minimal
        ([0.65, 0.25, 0.08, 0.02], 0),
        ([0.15, 0.70, 0.10, 0.05], 1), # Mild
        ([0.10, 0.60, 0.20, 0.10], 1),
        ([0.05, 0.15, 0.65, 0.15], 2), # Moderate
        ([0.08, 0.22, 0.55, 0.15], 2),
        ([0.02, 0.05, 0.18, 0.75], 3), # Severe
        ([0.01, 0.04, 0.15, 0.80], 3),
        ([0.45, 0.40, 0.10, 0.05], 1), # Ambiguous minimal vs mild (misclassification)
        ([0.05, 0.45, 0.40, 0.10], 2), # Ambiguous mild vs moderate
    ]

    raw_probs = [p for p, _ in np_rng]
    targets = [t for _, t in np_rng]

    # Uncalibrated (raw)
    raw_confs = [max(p) for p in raw_probs]
    raw_preds = [p.index(max(p)) for p in raw_probs]
    raw_accs = [1 if pred == tgt else 0 for pred, tgt in zip(raw_preds, targets)]
    raw_ece, _ = compute_ece(raw_confs, raw_accs, num_bins=5)
    raw_brier = compute_brier_score(raw_probs, targets)

    # Calibrated (T = 1.25)
    calib_probs = []
    labels = ["minimal", "mild", "moderate", "severe"]
    for p in raw_probs:
        p_dict = dict(zip(labels, p))
        c_dict = apply_temperature_scaling(p_dict, temperature=1.25)
        calib_probs.append([c_dict[k] for k in labels])

    calib_confs = [max(p) for p in calib_probs]
    calib_preds = [p.index(max(p)) for p in calib_probs]
    calib_accs = [1 if pred == tgt else 0 for pred, tgt in zip(calib_preds, targets)]
    calib_ece, _ = compute_ece(calib_confs, calib_accs, num_bins=5)
    calib_brier = compute_brier_score(calib_probs, targets)

    print(f"Uncalibrated (Raw Late Fusion) : ECE = {raw_ece:.4f} ({raw_ece*100:.1f}%), Brier = {raw_brier:.4f}")
    print(f"Calibrated (T = 1.25 Scaling)  : ECE = {calib_ece:.4f} ({calib_ece*100:.1f}%), Brier = {calib_brier:.4f}")
    print(f"ECE Improvement                : -{(raw_ece - calib_ece)*100:.1f}% calibration error reduction")


if __name__ == "__main__":
    run_weight_sensitivity()
    run_missingness_benchmark()
    run_saathi_benchmark()
    run_negation_benchmark()
    run_calibration_benchmark()
