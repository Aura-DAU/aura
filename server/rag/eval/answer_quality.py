"""Answer-level scoring for the RAG evaluation.

Source matching alone says nothing about whether the answer is right. These
checks are lexical and offline, so they run without a judge model:

- expected numbers (fees, credits, dates) must all appear in the answer;
- token F1 against the expected answer measures content overlap;
- an expected answer of NOT_FOUND means AURA must abstain;
- repeated runs of the same question must agree (consistency).
"""

import re
from collections import Counter

NOT_FOUND = "NOT_FOUND"

_ABSTAIN_PATTERNS = (
    "could not find",
    "couldn't find",
    "not available in the",
    "not documented",
    "no information",
    "not mentioned in",
    "do not contain",
    "does not contain",
)

_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "a an and are as at be by for from has have in is it of on or that the this to was were with".split()
)


def normalize_numbers(text: str) -> set[str]:
    return {m.group(0).replace(",", "").rstrip(".") for m in _NUMBER_RE.finditer(text or "")}


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOPWORDS]


def token_f1(expected: str, actual: str) -> float:
    exp, act = Counter(tokens(expected)), Counter(tokens(actual))
    overlap = sum((exp & act).values())
    if not exp or not act or not overlap:
        return 0.0
    precision = overlap / sum(act.values())
    recall = overlap / sum(exp.values())
    return 2 * precision * recall / (precision + recall)


def is_abstention(answer: str) -> bool:
    lowered = (answer or "").lower()
    return any(p in lowered for p in _ABSTAIN_PATTERNS)


def score_answer(expected: str, actual: str, min_f1: float = 0.3) -> dict:
    """Return {"correct", "numbers_ok", "f1", "abstained"} for one answer."""
    expected = (expected or "").strip()
    abstained = is_abstention(actual)
    if expected.upper() == NOT_FOUND:
        return {"correct": abstained, "numbers_ok": True, "f1": 0.0, "abstained": abstained}
    if not expected:
        return {"correct": None, "numbers_ok": None, "f1": None, "abstained": abstained}

    missing = normalize_numbers(expected) - normalize_numbers(actual)
    numbers_ok = not missing
    f1 = token_f1(expected, actual)
    correct = numbers_ok and not abstained and f1 >= min_f1
    return {"correct": correct, "numbers_ok": numbers_ok, "f1": round(f1, 3), "abstained": abstained}


def consistency(answers: list[str]) -> float:
    """Mean pairwise token Jaccard of repeated answers (1.0 = identical)."""
    sets = [set(tokens(a)) for a in answers if a]
    if len(sets) < 2:
        return 1.0
    scores = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            scores.append(len(sets[i] & sets[j]) / len(union) if union else 1.0)
    return sum(scores) / len(scores)
