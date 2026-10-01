import pytest

from services.negation_service import detect_crisis_intent


@pytest.mark.parametrize("text", [
    "I want to kill myself.",
    "I am going to end my life tonight.",
    "I don't want to live anymore.",
    "I am not okay, I want to kill myself.",
    "My friend was suicidal, but I want to die.",
    "I have been self-harming.",
    "I cut myself today.",
])
def test_affirmative_self_directed_crisis_language(text):
    assert detect_crisis_intent(text)["is_crisis"] is True


@pytest.mark.parametrize("text", [
    "I do not want to kill myself.",
    "I would never commit suicide.",
    "My friend wants to die and I am worried about her.",
    "I watched a movie about suicide.",
    "We were killing time before class.",
    "That joke made me die laughing.",
])
def test_negated_third_party_and_idiom_cases_are_suppressed(text):
    assert detect_crisis_intent(text)["is_crisis"] is False


@pytest.mark.parametrize("text", ["I feel hopeless.", "I feel worthless today."])
def test_distress_is_separate_from_crisis(text):
    result = detect_crisis_intent(text)
    assert result["distress"] is True
    assert result["is_crisis"] is False
