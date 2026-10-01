"""v2.1 = frozen v2 + self-harm expressions as crisis triggers (post hoc).
Motivation: PHQ-9 Item 9 covers 'thoughts ... of hurting yourself', so
self-harm statements should set the crisis flag, not only the distress flag.
This change was made after v2 had been scored on the test sets; it was not
tuned on test errors."""
import re
import crisis_v2 as base

SELF_HARM = [
    (r"\bself[-\s]?harm(?:ing|ed)?\b", False),
    (r"\b(?:hurt|hurting|cut|cutting|burn|burning|harm|harming)\s+myself\b", True),
]
EXPLICIT = base.EXPLICIT + SELF_HARM
DISTRESS = [r"\bhopeless(?:ness)?\b", r"\bworthless(?:ness)?\b"]

def detect(text, explicit=EXPLICIT, distress=DISTRESS):
    out = {"is_crisis": False, "distress": False, "trigger": None, "negated_hits": 0, "third_party_hits": 0}
    if not text or not text.strip():
        return out
    t = base.normalise(text)
    for idiom in base.IDIOMS:
        t = re.sub(idiom, " ", t)
    for clause in base._clauses(t):
        for pat, self_ref in explicit:
            for m in re.finditer(pat, clause):
                prefix = clause[:m.start()]
                if base._negated(prefix):
                    out["negated_hits"] += 1; continue
                if not self_ref and base._third_party(prefix):
                    out["third_party_hits"] += 1; continue
                out.update(is_crisis=True, trigger=m.group(0)); return out
        for pat in distress:
            m = re.search(pat, clause)
            if m and not base._negated(clause[:m.start()]) and not base._third_party(clause[:m.start()]):
                out["distress"] = True
    return out

def detect_crisis_intent(text):
    return detect(text)

# Ablation: v2 scoping rules with the v1 trigger vocabulary
V1_VOCAB = [(r"\bkill\s+myself\b", True), (r"\bkill\s+me\b", True), (r"\bend\s+my\s+life\b", True),
            (r"\bend\s+it\s+all\b", False), (r"\bwant\s+to\s+die\b", False), (r"\bwish\s+i\s+was\s+dead\b", True),
            (r"\bwish\s+i\s+were\s+dead\b", True), (r"\bbetter\s+off\s+dead\b", False), (r"\bcommit\s+suicide\b", False),
            (r"\btake\s+my\s+own\s+life\b", True), (r"\bno\s+reason\s+to\s+live\b", False), (r"\bdone\s+with\s+life\b", False)] + \
           [(rf"\b{re.escape(t)}\b", False) for t in ["suicide", "suicidal", "kill", "die", "hopeless", "worthless", "self-harm"]]

def detect_v2scope_v1vocab(text):
    return detect(text, explicit=V1_VOCAB, distress=[])
