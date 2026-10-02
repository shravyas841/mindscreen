"""
Linguistic Negation and Scope-Resolution Service
-------------------------------------------------
Provides context-aware crisis intent analysis for the MindScreen platform.

Addresses the critical failure mode of naive string matching by evaluating:
1. Preceding and succeeding negation scope (e.g., "I do NOT want to kill myself").
2. Third-party and non-self attributions (e.g., "My friend said she wants to die", "Watched a movie about suicide").
3. Idiomatic and benign usages (e.g., "kill time", "killing it at work").
"""

import re
from typing import Dict, Any, List, Optional

# Core crisis triggers categorized by severity
EXPLICIT_SUICIDAL_PHRASES = [
    r"\bkill\s+myself\b",
    r"\bkill\s+me\b",
    r"\bend\s+my\s+life\b",
    r"\bend\s+it\s+all\b",
    r"\bwant\s+to\s+die\b",
    r"\bwish\s+i\s+was\s+dead\b",
    r"\bwish\s+i\s+were\s+dead\b",
    r"\bbetter\s+off\s+dead\b",
    r"\bcommit\s+suicide\b",
    r"\btake\s+my\s+own\s+life\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bdone\s+with\s+life\b",
]

CRISIS_TOKENS = ["suicide", "suicidal", "kill", "die", "hopeless", "worthless", "self-harm"]

# Negation operators that invert or cancel the affirmative crisis assertion
NEGATION_OPERATORS = [
    "not", "don't", "dont", "do not", "never", "no", "hardly", "refuse",
    "refuse to", "haven't", "havent", "have not", "no desire", "no intention",
    "would never", "won't", "wont", "will not", "cannot", "can't", "cant",
    "stop thinking about", "without", "free of"
]

# Third-party / external attribution indicators
THIRD_PARTY_CUES = [
    "friend", "classmate", "roommate", "colleague", "sister", "brother",
    "someone", "somebody", "person", "they", "he said", "she said",
    "movie", "film", "documentary", "book", "article", "news", "show", "series", "video"
]

# Benign colloquial expressions that contain trigger words
BENIGN_COLLOQUIALISMS = [
    r"\bkill\s+time\b",
    r"\bkilling\s+it\b",
    r"\bkilling\s+me\s+with\s+laughter\b",
    r"\bdie\s+of\s+laughter\b",
    r"\bdie\s+laughing\b",
    r"\bdying\s+to\s+see\b",
    r"\bdying\s+to\s+know\b",
]


def detect_crisis_intent(text: str) -> Dict[str, Any]:
    """
    Analyzes text for true affirmative crisis intent with negation and scope resolution.

    Returns:
        {
            "is_crisis": bool,           # True only if affirmative self-crisis detected
            "trigger": str | None,       # Matched trigger expression
            "negated": bool,             # True if negation operator neutralized trigger
            "third_party": bool,         # True if attributed to third-party/media
            "colloquial": bool,          # True if benign colloquialism
            "confidence": float          # Estimated detection confidence [0.0, 1.0]
        }
    """
    clean_text = text.lower().strip()
    if not clean_text:
        return {
            "is_crisis": False,
            "trigger": None,
            "negated": False,
            "third_party": False,
            "colloquial": False,
            "confidence": 0.0,
        }

    # 1. Filter benign colloquialisms first
    for pattern in BENIGN_COLLOQUIALISMS:
        if re.search(pattern, clean_text):
            return {
                "is_crisis": False,
                "trigger": pattern,
                "negated": False,
                "third_party": False,
                "colloquial": True,
                "confidence": 0.95,
            }

    # 2. Check for multi-word explicit suicidal phrases
    matched_phrase = None
    for pattern in EXPLICIT_SUICIDAL_PHRASES:
        m = re.search(pattern, clean_text)
        if m:
            matched_phrase = m.group(0)
            phrase_start = m.start()
            
            # Check for negation in preceding 30 characters
            prefix = clean_text[max(0, phrase_start - 30):phrase_start]
            is_negated = any(re.search(rf"\b{re.escape(neg)}\b", prefix) for neg in NEGATION_OPERATORS)
            
            # Check for third-party context in the sentence
            is_third_party = any(re.search(rf"\b{re.escape(cue)}\b", clean_text) for cue in THIRD_PARTY_CUES)

            if is_negated:
                return {
                    "is_crisis": False,
                    "trigger": matched_phrase,
                    "negated": True,
                    "third_party": is_third_party,
                    "colloquial": False,
                    "confidence": 0.90,
                }
            if is_third_party:
                return {
                    "is_crisis": False,
                    "trigger": matched_phrase,
                    "negated": False,
                    "third_party": True,
                    "colloquial": False,
                    "confidence": 0.85,
                }

            # Affirmative direct suicidal expression
            return {
                "is_crisis": True,
                "trigger": matched_phrase,
                "negated": False,
                "third_party": False,
                "colloquial": False,
                "confidence": 0.98,
            }

    # 3. Check for single crisis keywords with windowed dependency scope
    words = re.findall(r"\b[a-zA-Z'\-]+\b", clean_text)
    for i, w in enumerate(words):
        if w in CRISIS_TOKENS:
            # Token window: 3 tokens before, 2 tokens after
            window_start = max(0, i - 3)
            window_end = min(len(words), i + 3)
            preceding_tokens = words[window_start:i]
            
            # Check negation in preceding window
            is_negated = any(tok in NEGATION_OPERATORS for tok in preceding_tokens)
            
            # Check third-party cues anywhere in window or sentence
            is_third_party = any(cue in words for cue in THIRD_PARTY_CUES)

            if is_negated:
                return {
                    "is_crisis": False,
                    "trigger": w,
                    "negated": True,
                    "third_party": is_third_party,
                    "colloquial": False,
                    "confidence": 0.85,
                }
            if is_third_party:
                return {
                    "is_crisis": False,
                    "trigger": w,
                    "negated": False,
                    "third_party": True,
                    "colloquial": False,
                    "confidence": 0.80,
                }

            # If isolated single keyword (e.g., "hopeless", "worthless"), check context
            # "hopeless" or "worthless" indicate severe distress but alone are less specific than explicit intent
            if w in ["hopeless", "worthless"]:
                return {
                    "is_crisis": True,
                    "trigger": w,
                    "negated": False,
                    "third_party": False,
                    "colloquial": False,
                    "confidence": 0.82,
                }

            # "suicide" or "kill"
            return {
                "is_crisis": True,
                "trigger": w,
                "negated": False,
                "third_party": False,
                "colloquial": False,
                "confidence": 0.92,
            }

    return {
        "is_crisis": False,
        "trigger": None,
        "negated": False,
        "third_party": False,
        "colloquial": False,
        "confidence": 0.0,
    }
