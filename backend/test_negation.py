import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.negation_service import detect_crisis_intent

test_cases = [
    ('I want to kill myself, I cannot handle this anymore.', True),
    ('I feel so hopeless and worthless every single day.', True),
    ('I am going to end my life tonight.', True),
    ('There is no reason to live for me.', True),
    ('I do not want to kill myself, I am just stressed about finals.', False),
    ('I would never commit suicide, I love my family.', False),
    ('I am not hopeless, things are slowly getting better.', False),
    ('My friend told me she wanted to die, I am so worried for her.', False),
    ('I watched a movie about suicide yesterday and it was very sad.', False),
    ('We were just trying to kill time before our flight.', False),
    ('I almost died laughing at that joke.', False)
]

passed = 0
for text, expected in test_cases:
    res = detect_crisis_intent(text)
    actual = res['is_crisis']
    status = 'PASS' if actual == expected else 'FAIL'
    if actual == expected:
        passed += 1
    neg = res['negated']
    tp = res['third_party']
    col = res['colloquial']
    print(f"[{status}] Expected: {str(expected):5s} | Got: {str(actual):5s} | Neg: {neg!s:5s} | 3rd: {tp!s:5s} | Col: {col!s:5s} | Text: {text}")

print(f"\nFinal: {passed}/{len(test_cases)} passed ({passed/len(test_cases)*100:.1f}%)")
