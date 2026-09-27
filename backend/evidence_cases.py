"""Constructed cases shared by tests and deterministic evidence generation.

These team-labeled statements verify bounded rule behavior. They are not
participant data and do not establish clinical sensitivity or specificity.
"""

CRISIS_CONFORMANCE_CASES = [
    ("A1", "I want to die.", True, "direct-first-person"),
    ("A2", "I want to end my life.", True, "direct-first-person"),
    ("A3", "I don't want to be alive anymore.", True, "direct-first-person"),
    ("A4", "I no longer want to live.", True, "direct-first-person"),
    ("A5", "I plan to overdose.", True, "direct-first-person"),
    ("M1", "I do not want to die, but now I want to kill myself.", True, "negation-then-affirmative"),
    ("M2", "I do not want to die, but I plan to overdose.", True, "negation-then-affirmative"),
    ("M3", "I never want to kill myself, yet I want to end my life.", True, "conflicting-scopes"),
    ("M4", "My friend says they want to die, but I want to die.", True, "third-party-then-first-person"),
    ("M5", 'My friend said "I want to die," but I want to end my life.', True, "quotation-then-first-person"),
    ("M6", "I was killing it at work, but now I want to die.", True, "idiom-then-affirmative"),
    ("M7", "I am not okay and I want to die.", True, "unrelated-negation-then-affirmative"),
    ("N1", "I don't want to die.", False, "genuine-negation"),
    ("N2", "I do not want to kill myself.", False, "genuine-negation"),
    ("N3", "I would never commit suicide.", False, "genuine-negation"),
    ("N4", "I have no intention to end my life.", False, "genuine-negation"),
    ("T1", "My friend said they want to die.", False, "third-party"),
    ("T2", "She told me she wants to kill herself.", False, "third-party"),
    ("Q1", 'My friend said "I want to die."', False, "quotation"),
    ("Q2", 'He said, "I plan to overdose."', False, "quotation"),
    ("I1", "I was killing it at work today.", False, "idiom"),
    ("I2", "That exam killed me.", False, "idiom"),
    ("I3", "We were trying to kill time.", False, "idiom"),
    ("I4", "We died laughing at the show.", False, "idiom"),
    ("U1", "I am not going to class because I feel tired.", False, "unrelated-negation"),
]
