"""Deterministic affirmative crisis-language safety gate.

This module resolves a small, documented set of first-person expressions. It is
an engineering safeguard, not a clinically validated suicide-risk model.
"""

import re
from typing import Any, Dict, Iterable, Iterator, Match, Optional, Tuple


AFFIRMATIVE_SPECIAL = [
    r"\bi\s+(?:do\s+not|don't|dont)\s+want\s+to\s+be\s+alive\s+anymore\b",
    r"\bi\s+no\s+longer\s+want\s+to\s+live\b",
]

AFFIRMATIVE_SELF_DIRECTED = [
    r"\bi\s+(?:really\s+)?want\s+to\s+die\b",
    r"\bi\s+(?:really\s+)?want\s+to\s+end\s+my\s+life\b",
    r"\bi\s+(?:am\s+)?going\s+to\s+end\s+my\s+life\b",
    r"\bi\s+plan\s+to\s+overdose\b",
    r"\bi\s+(?:am\s+)?planning\s+to\s+overdose\b",
    r"\bi\s+want\s+to\s+kill\s+myself\b",
    r"\bkill\s+myself\b",
    r"\bend\s+my\s+life\b",
    r"\bend\s+it\s+all\b",
    r"\bi\s+wish\s+i\s+(?:was|were)\s+dead\b",
    r"\bi(?:'m|\s+am)\s+better\s+off\s+dead\b",
    r"\bi\s+(?:will|am\s+going\s+to)\s+take\s+my\s+own\s+life\b",
    r"\bthere(?:'s|\s+is)\s+no\s+reason\s+(?:for\s+me\s+)?to\s+live\b",
    r"\bi(?:'m|\s+am)\s+done\s+with\s+life\b",
    r"\bi\s+(?:keep\s+)?think(?:ing)?\s+about\s+suicide\b",
    r"\bthinking\s+about\s+suicide\s+(?:constantly|all\s+the\s+time)\b",
    r"\bi\s+(?:want\s+to|plan\s+to)\s+self[- ]?harm\b",
]

NEGATED_CRISIS = [
    r"\bi\s+(?:do\s+not|don't|dont|never)\s+want\s+to\s+die\b",
    r"\bi\s+(?:do\s+not|don't|dont|never)\s+want\s+to\s+kill\s+myself\b",
    r"\bi\s+(?:would\s+never|will\s+not|won't|wont|refuse\s+to)\s+(?:commit\s+suicide|kill\s+myself|end\s+my\s+life)\b",
    r"\bi\s+have\s+no\s+(?:desire|intention)\s+to\s+(?:die|kill\s+myself|commit\s+suicide|end\s+my\s+life)\b",
    r"\bno\s+intention\s+of\s+(?:dying|self[- ]?harm)\b",
]

THIRD_PARTY_OR_QUOTED = [
    r"\b(?:my\s+)?(?:friend|classmate|roommate|colleague|sister|brother|mother|father)\s+(?:said|says|told\s+me|wrote|texted)(?:\s+that)?\s+(?:they|he|she)\s+(?:want|wants|wanted)\s+to\s+die\b",
    r"\b(?:she|he|they|someone|somebody)\s+(?:said|says|told\s+me|wrote|texted)(?:\s+that)?\s+(?:she|he|they)\s+(?:want|wants|wanted)\s+to\s+(?:die|kill\s+(?:herself|himself|themselves))\b",
    r"\b(?:she|he|they|my\s+friend)\s+(?:want|wants|wanted)\s+to\s+(?:die|kill\s+(?:herself|himself|themselves))\b",
    r"\b(?:movie|film|documentary|book|article|news|show|series|video)\b[^.!?]*(?:suicide|want(?:s|ed)?\s+to\s+die)\b",
]

BENIGN_IDIOMS = [
    r"\bkill\s+time\b",
    r"\bkilling\s+it\b",
    r"\bkilling\s+me\s+with\s+laughter\b",
    r"\b(?:die|died)\s+laughing\b",
    r"\bdie\s+of\s+laughter\b",
    r"\bdying\s+to\s+(?:see|know)\b",
    r"\bthat\s+(?:exam|test|workout|joke)\s+killed\s+me\b",
]


def _first_match(patterns: Iterable[str], text: str) -> Optional[Tuple[str, Match[str]]]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return pattern, match
    return None


def _ordered_matches(patterns: Iterable[str], text: str) -> Iterator[Match[str]]:
    """Yield all matches in text order, independent of pattern-list order."""
    matches = [
        match
        for pattern in patterns
        for match in re.finditer(pattern, text, flags=re.IGNORECASE)
    ]
    yield from sorted(matches, key=lambda match: (match.start(), match.end()))


def _mask_patterns(patterns: Iterable[str], text: str) -> Tuple[str, Optional[Match[str]]]:
    """Blank matched spans while retaining character offsets for scope checks."""
    matches = list(_ordered_matches(patterns, text))
    masked = list(text)
    for match in matches:
        masked[match.start():match.end()] = " " * (match.end() - match.start())
    return "".join(masked), (matches[0] if matches else None)


def _inside_quotes(text: str, position: int) -> bool:
    prefix = text[:position]
    return (prefix.count('"') % 2 == 1) or (prefix.count("“") > prefix.count("”"))


def _result(is_crisis: bool, trigger: Optional[str] = None, *, negated: bool = False,
            third_party: bool = False, colloquial: bool = False) -> Dict[str, Any]:
    return {
        "is_crisis": is_crisis,
        "trigger": trigger,
        "negated": negated,
        "third_party": third_party,
        "colloquial": colloquial,
        # Rule strength for debugging, not a calibrated probability.
        "confidence": 0.98 if is_crisis else (0.90 if trigger else 0.0),
    }


def detect_crisis_intent(text: str) -> Dict[str, Any]:
    """Detect supported affirmative, self-directed crisis expressions."""
    clean_text = " ".join((text or "").lower().strip().split())
    if not clean_text:
        return _result(False)

    # Mask only the negated span and continue. An earlier genuine negation must
    # not suppress a later, separately stated first-person affirmative intent.
    searchable, negated_match = _mask_patterns(NEGATED_CRISIS, clean_text)

    attributed = _first_match(THIRD_PARTY_OR_QUOTED, clean_text)

    # Mask idioms rather than returning early; later clauses still get checked.
    searchable, idiom_match = _mask_patterns(BENIGN_IDIOMS, searchable)

    quoted_match: Optional[Match[str]] = None
    affirmative_patterns = [*AFFIRMATIVE_SPECIAL, *AFFIRMATIVE_SELF_DIRECTED]
    for match in _ordered_matches(affirmative_patterns, searchable):
        if _inside_quotes(clean_text, match.start()):
            quoted_match = quoted_match or match
            continue
        return _result(True, match.group(0))

    if attributed:
        return _result(False, attributed[1].group(0), third_party=True)
    if quoted_match:
        return _result(False, quoted_match.group(0), third_party=True)
    if negated_match:
        return _result(False, negated_match.group(0), negated=True)
    if idiom_match:
        return _result(False, idiom_match.group(0), colloquial=True)
    return _result(False)
