"""
Crisis-intent filter, revision 2 (clause-scoped, ConText-style).

Changes relative to v1 (backend/services/negation_service.py):
  1. Scope is the clause, not a fixed 30-character window. Clauses end at
     sentence punctuation, commas/semicolons, and the conjunctions
     "but", "however", "though", "although", "yet", "except" (cf. ConText
     termination terms, Harkema et al. 2009).
  2. A negation cue suppresses a trigger only if it occurs in the same
     clause and at most NEG_WINDOW tokens before the trigger. Pseudo-negations
     ("can't stop", "not sure", "no longer", "don't know") never suppress.
     Cues that are frequent in affirmative crisis text ("cannot", "can't",
     "without", "no") were removed from the cue list; "no" only negates when it
     is part of "no intention/plan/desire/thought(s) of/to".
  3. Experiencer (third-party) suppression is clause-local: the trigger is
     attributed to someone else only when the nearest subject-like token that
     precedes it inside the clause is a third-party cue. Triggers with an
     inherent self-reference ("kill myself", "end my life") are never
     re-attributed. A third-party word elsewhere in the message no longer
     suppresses a first-person statement.
  4. Idioms are removed span-wise before matching instead of short-circuiting
     the whole message to "no crisis".
  5. Every trigger occurrence is evaluated; the message is flagged if ANY
     occurrence is affirmative and self-directed.
  6. Distress words ("hopeless", "worthless") no longer set the crisis flag.
     They are reported separately (distress=True) and may raise the text tier,
     but they are symptoms (PHQ-9 items 2 and 6), not suicidal intent.
  7. The explicit-phrase lexicon was extended (e.g. "don't want to live",
     "wanna die", "suicidal", "kill myself" inflections). Lexicon development
     used only the SDCNL training split and the constructed suite; the SDCNL
     test split and the Twitter corpus were held out.
"""
import re
from typing import Dict, Any, List

NEG_WINDOW = 5

# (pattern, has_inherent_self_reference)
EXPLICIT = [
    (r"\bkill(?:ing|ed)?\s+myself\b", True),
    (r"\bend(?:ing|ed)?\s+my\s+(?:own\s+)?life\b", True),
    (r"\btak(?:e|ing)\s+my\s+(?:own\s+)?life\b", True),
    (r"\bend(?:ing)?\s+it\s+(?:all|tonight|today|now|soon)\b", False),
    (r"\b(?:going|gonna|want|wanna|plan(?:ning)?|ready|decided)\s+(?:to\s+)?end\s+it\b", False),
    (r"\b(?:want|wanted|wanting|wanna|would\s+like|'d\s+like|ready)\s+(?:to\s+)?(?:just\s+|finally\s+|simply\s+)?die\b", False),
    (r"\bwish(?:ed)?\s+i\s+(?:was|were|had)\s+(?:dead|never\s+(?:been\s+)?born)\b", True),
    (r"\bwish(?:ed)?\s+i\s+(?:could\s+)?(?:just\s+)?(?:die|disappear|stop\s+existing|not\s+exist)\b", True),
    (r"\bwish\s+i\s+(?:had\s+)?never\s+(?:been\s+born|existed)\b", True),
    (r"\bbetter\s+off\s+dead\b", False),
    (r"\bbetter\s+off\s+without\s+me\b", True),
    (r"\bcommit(?:ting)?\s+suicide\b", False),
    (r"\bsuicid(?:e|al)\b", False),
    (r"\bno\s+(?:reason|point)\s+(?:to|in)\s+(?:live|living|being\s+alive|staying\s+alive)\b", False),
    (r"\b(?:don't|dont|do\s+not|no\s+longer)\s+(?:really\s+)?want\s+to\s+(?:live|be\s+alive|exist|wake\s+up|be\s+here)\b", False),
    (r"\bwhy\s+i\s+should\s+(?:be|stay)\s+alive\b", True),
    (r"\bdone\s+with\s+(?:life|living)\b", False),
    (r"\bcan't\s+go\s+on\b", False),
    (r"\bno\s+(?:other\s+)?way\s+out\b", False),
    (r"\bnoose\b", False),
    (r"\bsuicide\s+note\b", False),
    (r"\b(?:hang|hanging|overdos(?:e|ing)\s+on|shoot|shooting)\s+myself\b", True),
    (r"\bslit(?:ting)?\s+my\s+wrists?\b", True),
]

DISTRESS = [r"\bhopeless(?:ness)?\b", r"\bworthless(?:ness)?\b", r"\bself[-\s]?harm(?:ing)?\b"]

IDIOMS = [
    r"\bkill(?:ing)?\s+time\b", r"\bkilling\s+it\b", r"\bkilling\s+me\s+with\s+laughter\b",
    r"\bdie\s+of\s+laughter\b", r"\b(?:die|died|dying)\s+laughing\b",
    r"\bdying\s+to\s+(?:see|know|try|meet|go|hear|get)\b", r"\bto\s+die\s+for\b",
]

# Negation cues (single or multi-token). Deliberately excludes "no", "cannot",
# "can't", "without", which occur frequently in affirmative crisis statements.
NEG_CUES = [
    "not", "don't", "dont", "do not", "never", "won't", "wont", "will not",
    "wouldn't", "wouldnt", "would never", "didn't", "didnt", "no intention",
    "no intentions", "no plan", "no plans", "no desire", "no thoughts of",
    "no thought of", "refuse to", "refuse", "haven't", "havent", "have not",
]
# Pseudo-negations: contain a cue but do not negate the trigger.
PSEUDO_NEG = [
    r"\bcan'?t\s+stop\b", r"\bnot\s+sure\b", r"\bdon'?t\s+know\b", r"\bnot\s+only\b",
    r"\bnot\s+okay\b", r"\bnot\s+ok\b", r"\bnot\s+fine\b", r"\bnot\s+anymore\b",
    r"\bnever\s+(?:felt|been)\s+(?:so|this)\b", r"\bdon'?t\s+care\b",
    r"\bnot\s+(?:going|gonna)\s+to\s+lie\b", r"\bnot\s+gonna\s+lie\b",
]

FIRST_PERSON = {"i", "i'm", "im", "i've", "ive", "i'd", "id", "i'll", "me", "my", "myself", "we"}
THIRD_PARTY = {
    "he", "she", "they", "him", "her", "them", "his", "their", "he's", "she's", "they're",
    "friend", "friends", "classmate", "roommate", "colleague", "sister", "brother",
    "mom", "mother", "dad", "father", "son", "daughter", "girlfriend", "boyfriend",
    "wife", "husband", "cousin", "someone", "somebody", "people", "person", "character",
    "movie", "film", "documentary", "book", "article", "news", "show", "series", "video",
    "song", "episode",
}

CLAUSE_SPLIT = re.compile(
    r"[.!?;:\n,]+|\b(?:but|however|though|although|yet|except)\b", re.IGNORECASE)
TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")


def normalise(text: str) -> str:
    t = text.lower()
    t = t.replace("’", "'").replace("‘", "'")
    # tokenised corpora split contractions: "don t" -> "don't", "i m" -> "i'm"
    t = re.sub(r"\b(don|can|won|didn|isn|wasn|doesn|couldn|wouldn|shouldn|haven|aren) t\b", r"\1't", t)
    t = re.sub(r"\bi m\b", "i'm", t)
    t = re.sub(r"\bi ve\b", "i've", t)
    return t


def _clauses(text: str) -> List[str]:
    return [c.strip() for c in CLAUSE_SPLIT.split(text) if c and c.strip()]


def _negated(prefix: str) -> bool:
    """prefix = clause text before the trigger."""
    for p in PSEUDO_NEG:
        prefix = re.sub(p, " ", prefix)
    toks = TOKEN.findall(prefix)
    window = " ".join(toks[-NEG_WINDOW:])
    return any(re.search(rf"(?:^|\s){re.escape(c)}(?:\s|$)", window) for c in NEG_CUES)


def _third_party(prefix: str) -> bool:
    toks = TOKEN.findall(prefix)
    for tok in reversed(toks):
        if tok in FIRST_PERSON:
            return False
        if tok in THIRD_PARTY:
            return True
    return False


def detect_crisis_intent(text: str) -> Dict[str, Any]:
    out = {"is_crisis": False, "distress": False, "trigger": None,
           "negated_hits": 0, "third_party_hits": 0}
    if not text or not text.strip():
        return out
    t = normalise(text)
    for idiom in IDIOMS:
        t = re.sub(idiom, " ", t)
    for clause in _clauses(t):
        for pat, self_ref in EXPLICIT:
            for m in re.finditer(pat, clause):
                prefix = clause[:m.start()]
                if _negated(prefix):
                    out["negated_hits"] += 1
                    continue
                if not self_ref and _third_party(prefix):
                    out["third_party_hits"] += 1
                    continue
                out["is_crisis"] = True
                out["trigger"] = m.group(0)
                return out
        for pat in DISTRESS:
            m = re.search(pat, clause)
            if m and not _negated(clause[:m.start()]) and not _third_party(clause[:m.start()]):
                out["distress"] = True
    return out


if __name__ == "__main__":
    import sys
    for s in sys.argv[1:]:
        print(s, "->", detect_crisis_intent(s))
